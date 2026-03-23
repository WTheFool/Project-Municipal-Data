import React from "react";

interface ReportBuilderProps {
  reportData: any; // JSON or structured report from backend
}

export default function ReportBuilder({ reportData }: ReportBuilderProps) {
  if (!reportData) return null;

  return (
    <div className="p-4 border rounded shadow-sm bg-white mt-4">
      <h2 className="text-xl font-bold mb-2">Report Summary</h2>
      {reportData.sections?.map((section: any, idx: number) => (
        <div key={idx} className="mb-4">
          <h3 className="font-semibold">{section.title}</h3>
          <p>{section.content}</p>
          {section.table && (
            <table className="table-auto border-collapse border border-gray-300 mt-2 w-full">
              <thead>
                <tr>
                  {Object.keys(section.table[0]).map((col) => (
                    <th
                      key={col}
                      className="border border-gray-300 px-2 py-1 text-left"
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {section.table.map((row: any, rIdx: number) => (
                  <tr key={rIdx}>
                    {Object.values(row).map((val, vIdx) => (
                      <td key={vIdx} className="border border-gray-300 px-2 py-1">
                        {val}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      ))}
    </div>
  );
}