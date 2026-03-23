from rq import get_current_job
from municipal_core.pipeline.analysis_pipeline import AnalysisPipeline
from typing import List

def update_progress(percent: int):
    """
    Helper to update RQ job progress.
    """
    job = get_current_job()
    if job:
        job.meta['progress'] = percent
        job.save_meta()

def analysis_task(filepaths: List[str]):
    """
    Background task that runs the full analysis pipeline.
    Input: list of file paths to Excel files.
    Returns: dictionary with profile, stats, ML results, graphs, report, exports.
    """
    pipeline = AnalysisPipeline()

    update_progress(0)
    df = pipeline._read_files(filepaths)
    update_progress(10)

    df_std = pipeline._standardize(df)
    update_progress(30)

    profile = pipeline._profile(df_std)
    update_progress(40)

    df_features, indicators = pipeline._compute_indicators(df_std)
    update_progress(60)

    stats = pipeline._compute_stats(df_features)
    update_progress(70)

    ml_results = pipeline._run_ml(df_features)
    update_progress(80)

    graphs = pipeline._generate_graphs(df_features)
    update_progress(90)

    report = pipeline._generate_report(profile, stats, ml_results)
    update_progress(95)

    exports = pipeline._export(df_features, stats, indicators, graphs, report)
    update_progress(100)

    return {
        "profile": profile,
        "stats": stats,
        "ml_results": ml_results,
        "graphs": graphs,
        "report": report,
        **exports
    }