import io
import json
import os
import tempfile
from datetime import datetime
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session
import base64

from municipal_core.ingest.excel_reader import ExcelReader
from municipal_core.standardize.typing_engine import TypingEngine
from municipal_core.analytics.features.indicator_engine import IndicatorEngine
from municipal_core.analytics.stats_engine import StatsEngine
from municipal_core.analytics.ml_engine import MLEngine
from municipal_core.ai_services.graph_generator import GraphGenerator
from municipal_core.exports.word_exporter import WordExporter

from municipal_worker.infra.db import SessionLocal
from municipal_worker.infra.storage_s3 import s3_client
from municipal_worker.infra.settings import settings
from municipal_worker.infra.models.run import Run
from municipal_worker.infra.models.artifact import RunArtifact

def _set_status(db: Session, run_id: str, status: str, error: str | None = None):
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise RuntimeError(f"Run not found: {run_id}")
    run.status = status
    run.error = error
    if status == "running":
        run.started_at = datetime.utcnow()
    if status in ("completed", "failed"):
        run.finished_at = datetime.utcnow()
    db.commit()

def _add_artifact(db: Session, run_id: str, kind: str, storage_key: str):
    db.add(RunArtifact(run_id=run_id, kind=kind, storage_key=storage_key, created_at=datetime.utcnow()))
    db.commit()

def _profile(df: pd.DataFrame) -> dict:
    return {
        "rows": int(len(df)),
        "columns": list(df.columns),
        "missing": df.isnull().sum().to_dict(),
    }

def _to_jsonable(obj: Any):
    # Convert common pandas/numpy objects into plain JSON types.
    if isinstance(obj, pd.Series):
        return obj.tolist()
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="records")
    if isinstance(obj, (pd.Timestamp, datetime)):
        return obj.isoformat()
    return obj

def _forecast_next_years(df: pd.DataFrame, years_ahead: int = 3, explicit_years: dict[str, int] | None = None) -> dict:
    """
    Very lightweight forecasting:
    - find a year column (name contains 'year') or a datetime column
    - aggregate numeric columns by year (mean)
    - fit a linear trend and predict next N years
    - confidence is a crude percent based on R^2
    """
    import numpy as np

    # If caller provided an explicit year per dataset (e.g., each uploaded file corresponds to a year),
    # build a time series from dataset-level aggregates.
    if explicit_years:
        if "source_file" not in df.columns:
            return {"message": "Missing source_file for forecasting."}
        import numpy as np

        def _find_col(substrs: list[str]) -> str | None:
            for c in df.columns:
                cl = str(c).lower()
                for s in substrs:
                    if s in cl:
                        return str(c)
            return None

        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        numeric_cols = [c for c in numeric_cols if not c.startswith("__")]
        if not numeric_cols:
            return {"message": "No numeric columns to forecast."}

        rows = []
        for label, yr in explicit_years.items():
            g = df[df["source_file"] == label]
            if g.empty:
                continue
            row = {"__year": int(yr)}
            for c in numeric_cols:
                row[c] = float(pd.to_numeric(g[c], errors="coerce").mean())
            rows.append(row)
        if len(rows) < 2:
            return {"message": "Need at least 2 yearly datasets to forecast."}
        by_year = pd.DataFrame(rows).groupby("__year")[numeric_cols].mean(numeric_only=True).sort_index()

        x = by_year.index.to_numpy(dtype=float)
        next_years = [int(x[-1] + i) for i in range(1, years_ahead + 1)]
        out: dict[str, Any] = {
            "year_source": "upload_years",
            "years": by_year.index.astype(int).tolist(),
            "forecast": {},
        }
        for col in numeric_cols:
            y = by_year[col].to_numpy(dtype=float)
            if np.all(np.isnan(y)):
                continue
            mask = ~np.isnan(y)
            if mask.sum() < 2:
                continue
            coeff = np.polyfit(x[mask], y[mask], deg=1)
            yhat = np.polyval(coeff, x[mask])
            ss_res = float(np.sum((y[mask] - yhat) ** 2))
            ss_tot = float(np.sum((y[mask] - float(np.mean(y[mask]))) ** 2))
            r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
            conf = max(0.0, min(1.0, r2)) * 100.0
            pred = [float(np.polyval(coeff, float(yr))) for yr in next_years]
            out["forecast"][col] = {
                "model": "linear_trend",
                "confidence_pct": round(conf, 1),
                "history": [float(v) if pd.notna(v) else None for v in by_year[col].tolist()],
                "next_years": next_years,
                "predicted": pred,
            }

        # Optional: per-group forecasts for mayor-friendly breakdowns (region/crop),
        # but only when we can detect a grouping column.
        region_col = _find_col(["region", "prefecture", "municip", "district", "περιοχ", "δημος", "δήμος", "περιφερ"])
        crop_col = _find_col(["cultivation", "crop", "καλλιεργ", "καλλιέργ", "ειδοσ", "είδος"])
        area_col = _find_col(["area", "strem", "στρεμ", "στρέμ", "εκταση", "έκταση", "εμβαδ"])
        water_col = _find_col(["water", "volume", "καταναλ", "κατανάλ", "ογκο", "όγκο", "m3"])

        def _group_forecast(group_col: str, value_col: str, agg: str = "mean", top_n: int = 10) -> dict[str, Any]:
            work = df[[group_col, value_col, "source_file"]].copy()
            work["__year"] = work["source_file"].map(explicit_years)
            work = work.dropna(subset=["__year"])
            work[value_col] = pd.to_numeric(work[value_col], errors="coerce")
            if work.empty:
                return {}

            # pick largest groups by overall magnitude (sum) to keep output readable
            sizes = work.groupby(group_col)[value_col].sum(min_count=1).sort_values(ascending=False)
            top_groups = [g for g in sizes.head(top_n).index.tolist() if pd.notna(g)]
            if not top_groups:
                return {}

            out_g: dict[str, Any] = {}
            for g in top_groups:
                sub = work[work[group_col] == g]
                if sub.empty:
                    continue
                by = sub.groupby("__year")[value_col].agg(agg).sort_index()
                if len(by.index) < 2:
                    continue
                xx = by.index.to_numpy(dtype=float)
                yy = by.to_numpy(dtype=float)
                m = ~np.isnan(yy)
                if m.sum() < 2:
                    continue
                coeff = np.polyfit(xx[m], yy[m], deg=1)
                yhat = np.polyval(coeff, xx[m])
                ss_res = float(np.sum((yy[m] - yhat) ** 2))
                ss_tot = float(np.sum((yy[m] - float(np.mean(yy[m]))) ** 2))
                r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
                conf2 = max(0.0, min(1.0, r2)) * 100.0
                pred2 = [float(np.polyval(coeff, float(yr))) for yr in next_years]
                out_g[str(g)] = {
                    "model": "linear_trend",
                    "confidence_pct": round(conf2, 1),
                    "years": by.index.astype(int).tolist(),
                    "history": [float(v) if pd.notna(v) else None for v in by.tolist()],
                    "next_years": next_years,
                    "predicted": pred2,
                }
            return out_g

        group_forecasts: dict[str, Any] = {}
        if region_col and area_col:
            gf = _group_forecast(region_col, area_col, agg="mean")
            if gf:
                group_forecasts["avg_area_by_region"] = {"group_col": region_col, "value_col": area_col, "items": gf}
        if crop_col and area_col:
            gf = _group_forecast(crop_col, area_col, agg="mean")
            if gf:
                group_forecasts["avg_area_by_crop"] = {"group_col": crop_col, "value_col": area_col, "items": gf}
        if region_col and water_col:
            gf = _group_forecast(region_col, water_col, agg="mean")
            if gf:
                group_forecasts["avg_water_by_region"] = {"group_col": region_col, "value_col": water_col, "items": gf}
        if crop_col and water_col:
            gf = _group_forecast(crop_col, water_col, agg="mean")
            if gf:
                group_forecasts["avg_water_by_crop"] = {"group_col": crop_col, "value_col": water_col, "items": gf}

        if group_forecasts:
            out["group_forecast"] = group_forecasts
        return out

    year_col = next((c for c in df.columns if "year" in c.lower()), None)
    if year_col is None:
        dt_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
        year_col = dt_cols[0] if dt_cols else None

    if year_col is None:
        return {"message": "No year/date column found for forecasting. Tip: specify a year for each uploaded file."}

    s = df[year_col]
    if pd.api.types.is_datetime64_any_dtype(s):
        years = pd.to_datetime(s, errors="coerce").dt.year
    else:
        years = pd.to_numeric(s, errors="coerce").astype("Int64")

    work = df.copy()
    work["__year"] = years
    work = work.dropna(subset=["__year"])
    if work.empty:
        return {"message": "Year/date column had no usable values."}

    numeric_cols = work.select_dtypes(include="number").columns.tolist()
    numeric_cols = [c for c in numeric_cols if c != "__year"]
    if not numeric_cols:
        return {"message": "No numeric columns to forecast."}

    by_year = work.groupby("__year")[numeric_cols].mean(numeric_only=True).sort_index()
    if len(by_year.index) < 2:
        return {"message": "Need at least 2 years of data to forecast."}

    x = by_year.index.to_numpy(dtype=float)
    next_years = [int(x[-1] + i) for i in range(1, years_ahead + 1)]

    out: dict[str, Any] = {"year_column": year_col, "years": by_year.index.astype(int).tolist(), "forecast": {}}
    for col in numeric_cols:
        y = by_year[col].to_numpy(dtype=float)
        if np.all(np.isnan(y)):
            continue
        mask = ~np.isnan(y)
        if mask.sum() < 2:
            continue
        coeff = np.polyfit(x[mask], y[mask], deg=1)
        yhat = np.polyval(coeff, x[mask])
        ss_res = float(np.sum((y[mask] - yhat) ** 2))
        ss_tot = float(np.sum((y[mask] - float(np.mean(y[mask]))) ** 2))
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        conf = max(0.0, min(1.0, r2)) * 100.0
        pred = [float(np.polyval(coeff, float(yr))) for yr in next_years]
        out["forecast"][col] = {
            "model": "linear_trend",
            "confidence_pct": round(conf, 1),
            "next_years": next_years,
            "predicted": pred,
        }
    return out


def _summary_averages(df: pd.DataFrame) -> dict:
    """
    Human-friendly averages.
    Tries to compute:
    - avg area per cultivation/crop (if a crop-like column exists)
    - avg water per area (if water & area exist)
    - per-crop averages of the above
    """
    def _find_col(substrs: list[str], candidates: list[str]) -> str | None:
        for s in substrs:
            for c in candidates:
                if s in c.lower():
                    return c
        return None

    cols = list(df.columns)
    crop_col = _find_col(["cultivation", "crop", "καλλιεργ", "καλλιέργ", "ειδοσ", "είδος"], cols)
    area_col = _find_col(["area", "strem", "στρεμ", "στρέμ", "εκταση", "έκταση", "εμβαδ"], cols)
    water_col = _find_col(["water", "volume", "καταναλ", "κατανάλ", "ογκο", "όγκο", "m3"], cols)

    out: dict[str, Any] = {"detected": {"crop_col": crop_col, "area_col": area_col, "water_col": water_col}}

    if area_col and pd.api.types.is_numeric_dtype(df[area_col]):
        out["avg_area"] = float(pd.to_numeric(df[area_col], errors="coerce").mean())
        out["total_area"] = float(pd.to_numeric(df[area_col], errors="coerce").sum(min_count=1))
    if water_col and area_col and pd.api.types.is_numeric_dtype(df[water_col]) and pd.api.types.is_numeric_dtype(df[area_col]):
        w = pd.to_numeric(df[water_col], errors="coerce")
        a = pd.to_numeric(df[area_col], errors="coerce").replace(0, pd.NA)
        out["avg_water_per_area"] = float((w / a).mean())

    # Region-level summary (more interpretable than "avg area per row by region")
    region_col = _find_col(
        ["region", "prefecture", "municip", "district", "περιοχ", "δημος", "δήμος", "περιφερ", "κοινοτ"],
        cols,
    )
    if region_col:
        vc = df[region_col].astype(str)
        out["region_field_count"] = vc.value_counts(dropna=True).to_dict()
        out["avg_field_count_per_region"] = float(pd.Series(out["region_field_count"]).mean()) if out["region_field_count"] else 0.0
        if area_col and area_col in df.columns:
            s = pd.to_numeric(df[area_col], errors="coerce")
            totals = df.assign(__area=s).groupby(region_col)["__area"].sum(min_count=1).dropna()
            out["region_total_area"] = {str(k): float(v) for k, v in totals.to_dict().items()}
            out["avg_total_area_per_region"] = float(totals.mean()) if not totals.empty else 0.0

    if crop_col:
        grp = df.groupby(crop_col, dropna=True)
        per_crop: dict[str, Any] = {}
        if area_col and area_col in df.columns:
            per_crop["avg_area_by_crop"] = (
                grp[area_col].apply(lambda s: float(pd.to_numeric(s, errors="coerce").mean())).to_dict()
            )
            totals = grp[area_col].apply(lambda s: float(pd.to_numeric(s, errors="coerce").sum(min_count=1))).to_dict()
            per_crop["total_area_by_crop"] = totals
        if water_col and area_col and water_col in df.columns and area_col in df.columns:
            def _wpa(g: pd.DataFrame) -> float:
                w = pd.to_numeric(g[water_col], errors="coerce")
                a = pd.to_numeric(g[area_col], errors="coerce").replace(0, pd.NA)
                return float((w / a).mean())
            per_crop["avg_water_per_area_by_crop"] = grp.apply(_wpa).to_dict()
        if per_crop:
            out["per_crop"] = per_crop

    return out


def _forecast_charts_png(forecast: dict) -> dict[str, str]:
    """
    Turn forecast JSON into simple line charts (base64 PNG):
    historical years on the left, predicted on the right.
    """
    import matplotlib.pyplot as plt

    if not isinstance(forecast, dict) or "forecast" not in forecast:
        return {}
    years = forecast.get("years") or []
    fc = forecast.get("forecast") or {}
    if not years or not isinstance(fc, dict):
        return {}

    out: dict[str, str] = {}
    for metric, spec in fc.items():
        try:
            next_years = spec.get("next_years") or []
            predicted = spec.get("predicted") or []
            if not next_years or not predicted:
                continue
            fig, ax = plt.subplots(figsize=(7, 4))
            hist = spec.get("history") or []
            if hist and isinstance(hist, list) and len(hist) == len(years):
                ax.plot(years, hist, marker="o", label="History")
                ax.plot(next_years, predicted, marker="o", label="Predicted")
                ax.legend()
            else:
                ax.plot(next_years, predicted, marker="o")
            ax.set_title(f"Prediction: {metric} (conf={spec.get('confidence_pct','?')}%)")
            ax.set_xlabel("Year")
            ax.set_ylabel(metric)
            fig.tight_layout()
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight")
            buf.seek(0)
            out[f"forecast_{metric}"] = base64.b64encode(buf.getvalue()).decode("utf-8")
            plt.close(fig)
        except Exception:
            continue

    # Group-level charts (region/crop) if present
    gf = forecast.get("group_forecast") if isinstance(forecast, dict) else None
    if isinstance(gf, dict):
        for key, spec in gf.items():
            try:
                items = spec.get("items")
                if not isinstance(items, dict) or not items:
                    continue
                # chart: top 6 groups, predicted series only to keep readable
                fig, ax = plt.subplots(figsize=(8, 4))
                for name, it in list(items.items())[:6]:
                    ny = it.get("next_years") or []
                    pr = it.get("predicted") or []
                    if ny and pr:
                        ax.plot(ny, pr, marker="o", label=str(name))
                ax.set_title(f"Predictions by group: {key}")
                ax.set_xlabel("Year")
                ax.set_ylabel(str(spec.get("value_col") or "value"))
                ax.legend(fontsize=8)
                fig.tight_layout()
                buf = io.BytesIO()
                fig.savefig(buf, format="png", bbox_inches="tight")
                buf.seek(0)
                out[f"group_forecast_{key}"] = base64.b64encode(buf.getvalue()).decode("utf-8")
                plt.close(fig)
            except Exception:
                continue
    return out


def _export_graphs_excel(graphs: dict) -> str:
    """
    Create a graphs-only Excel workbook (no raw data sheets).
    Expects graphs in the form: { 'compare': {name: b64png, ...}, 'datasets': {...} }
    """
    import xlsxwriter

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    wb = xlsxwriter.Workbook(tmp.name)

    def _add_sheet(title: str, g: dict[str, str]):
        ws = wb.add_worksheet(title[:31])
        ws.set_column(0, 0, 2)
        ws.set_column(1, 20, 18)
        row = 0
        col = 0
        max_cols = 2
        for name, b64 in g.items():
            try:
                img = base64.b64decode(b64)
            except Exception:
                continue
            ws.write(row, col, name)
            ws.insert_image(row + 1, col, name + ".png", {"image_data": io.BytesIO(img), "x_scale": 0.9, "y_scale": 0.9})
            col += 8
            if (col // 8) >= max_cols:
                col = 0
                row += 22

    compare = graphs.get("compare") if isinstance(graphs, dict) else None
    datasets = graphs.get("datasets") if isinstance(graphs, dict) else None

    if isinstance(compare, dict):
        _add_sheet("Compare", compare)

    if isinstance(datasets, dict):
        for k, v in datasets.items():
            if isinstance(v, dict):
                _add_sheet(str(k), v)

    wb.close()
    return tmp.name

def standardize_run(
    run_id: str,
    project_id: str,
    upload_storage_keys: list[str],
    years: list[int] | None = None,
    graph_mode: str = "municipal",
) -> dict:
    db = SessionLocal()
    s3 = s3_client()
    try:
        _set_status(db, run_id, "running")

        # ---- 1) Read all uploads from S3 into DataFrames ----
        reader = ExcelReader()
        dfs: list[pd.DataFrame] = []
        year_by_dataset: dict[str, int] = {}
        for idx, key in enumerate(upload_storage_keys):
            obj = s3.get_object(Bucket=settings.s3_bucket, Key=key)
            excel_bytes = obj["Body"].read()
            filename = os.path.basename(key)
            df = reader.read(io.BytesIO(excel_bytes), filename=filename)
            df = df.copy()
            label = f"Dataset_{idx+1}"
            df["source_file"] = label
            df["__source_key"] = key
            if years and idx < len(years) and years[idx] is not None:
                year_by_dataset[label] = int(years[idx])
                # Provide a per-row year for time-trend graphs.
                df["__upload_year"] = int(years[idx])
            dfs.append(df)

        if not dfs:
            raise RuntimeError("No input files.")

        # ---- 2) Standardize for comparison: intersect common columns and concatenate ----
        common_cols = list(set.intersection(*(set(df.columns) for df in dfs)))
        if len(dfs) > 1 and not common_cols:
            raise RuntimeError("No common columns found across the uploaded files.")
        use_cols = common_cols if len(dfs) > 1 else list(dfs[0].columns)
        df_all = pd.concat([d[use_cols] for d in dfs], ignore_index=True)

        # ---- 3) Indicators / stats / ML / graphs ----
        typing_engine = TypingEngine()
        variables = typing_engine.infer_variables(df_all)
        indicator_defs = IndicatorEngine.create_default_irrigation_indicators(variables)
        ind_engine = IndicatorEngine(indicators=indicator_defs)
        indicators = ind_engine.compute_all(df_all)
        df_features = pd.concat([df_all, indicators], axis=1)

        stats = StatsEngine().compute(df_features)

        numeric_cols = df_features.select_dtypes(include="number").columns.tolist()
        ml_raw = MLEngine().detect_patterns(df_features, numeric_columns=numeric_cols) if numeric_cols else {}
        ml_results = {k: _to_jsonable(v) for k, v in ml_raw.items()}

        # Graphs: per dataset + combined comparison.
        gg = GraphGenerator()
        mode = (graph_mode or "municipal").strip().lower()
        graphs_compare = gg.generate(df_features, compare_mode=(len(dfs) > 1), mode=mode)
        graphs_by_dataset: dict[str, Any] = {}
        for label, g in df_features.groupby("source_file"):
            graphs_by_dataset[str(label)] = gg.generate(g, compare_mode=False, mode=mode)
        graphs = {"compare": graphs_compare, "datasets": graphs_by_dataset}

        forecast = _forecast_next_years(df_features, years_ahead=3, explicit_years=year_by_dataset or None)
        summary = _summary_averages(df_features)

        forecast_graphs = _forecast_charts_png(forecast)
        if forecast_graphs:
            # attach forecast graphs under graphs for rendering + export
            graphs.setdefault("forecast", forecast_graphs)

        # ---- 4) Store core artifacts in S3 + DB ----
        parquet_buf = io.BytesIO()
        df_features.to_parquet(parquet_buf, index=False)
        parquet_key = f"projects/{project_id}/runs/{run_id}/standardized.parquet"
        s3.put_object(Bucket=settings.s3_bucket, Key=parquet_key, Body=parquet_buf.getvalue())
        _add_artifact(db, run_id, "standardized_parquet", parquet_key)

        profile_key = f"projects/{project_id}/runs/{run_id}/profile.json"
        s3.put_object(
            Bucket=settings.s3_bucket,
            Key=profile_key,
            Body=json.dumps(_profile(df_features), ensure_ascii=False, indent=2, default=_to_jsonable).encode("utf-8"),
            ContentType="application/json",
        )
        _add_artifact(db, run_id, "profile_json", profile_key)

        stats_key = f"projects/{project_id}/runs/{run_id}/stats.json"
        s3.put_object(
            Bucket=settings.s3_bucket,
            Key=stats_key,
            Body=json.dumps(stats, ensure_ascii=False, indent=2).encode("utf-8"),
            ContentType="application/json",
        )
        _add_artifact(db, run_id, "stats_json", stats_key)

        ml_key = f"projects/{project_id}/runs/{run_id}/ml.json"
        s3.put_object(
            Bucket=settings.s3_bucket,
            Key=ml_key,
            Body=json.dumps(ml_results, ensure_ascii=False, indent=2).encode("utf-8"),
            ContentType="application/json",
        )
        _add_artifact(db, run_id, "ml_json", ml_key)

        graphs_key = f"projects/{project_id}/runs/{run_id}/graphs.json"
        s3.put_object(
            Bucket=settings.s3_bucket,
            Key=graphs_key,
            Body=json.dumps(graphs, ensure_ascii=False).encode("utf-8"),
            ContentType="application/json",
        )
        _add_artifact(db, run_id, "graphs_json", graphs_key)

        forecast_key = f"projects/{project_id}/runs/{run_id}/forecast.json"
        s3.put_object(
            Bucket=settings.s3_bucket,
            Key=forecast_key,
            Body=json.dumps(forecast, ensure_ascii=False, indent=2).encode("utf-8"),
            ContentType="application/json",
        )
        _add_artifact(db, run_id, "forecast_json", forecast_key)

        summary_key = f"projects/{project_id}/runs/{run_id}/summary.json"
        s3.put_object(
            Bucket=settings.s3_bucket,
            Key=summary_key,
            Body=json.dumps(summary, ensure_ascii=False, indent=2).encode("utf-8"),
            ContentType="application/json",
        )
        _add_artifact(db, run_id, "summary_json", summary_key)

        # ---- 5) Export graphs-only Excel and store ----
        temp_xlsx = _export_graphs_excel(graphs)
        with open(temp_xlsx, "rb") as f:
            excel_key = f"projects/{project_id}/runs/{run_id}/export.xlsx"
            s3.put_object(
                Bucket=settings.s3_bucket,
                Key=excel_key,
                Body=f.read(),
                ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        _add_artifact(db, run_id, "excel_export", excel_key)

        # ---- 6) Export Word report (graphs + stats) and store ----
        # Use the compare graphs in Word (keeps the report concise).
        word_graphs = graphs.get("compare") if isinstance(graphs, dict) else {}
        word_path = WordExporter().export(report="Municipal run report", graphs=word_graphs, stats=stats)
        with open(word_path, "rb") as f:
            word_key = f"projects/{project_id}/runs/{run_id}/export.docx"
            s3.put_object(
                Bucket=settings.s3_bucket,
                Key=word_key,
                Body=f.read(),
                ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        _add_artifact(db, run_id, "word_export", word_key)

        _set_status(db, run_id, "completed")
        return {"ok": True, "run_id": run_id, "rows": int(len(df_features)), "file_count": len(dfs)}
    except Exception as e:
        db.rollback()
        _set_status(db, run_id, "failed", error=str(e))
        raise
    finally:
        db.close()
