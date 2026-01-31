"use client";

import { cn } from "@/lib/utils";
import { getRiskColor, getRiskLevel } from "@/lib/chart-colors";

export interface RiskCell {
  impact: number; // 1-5
  likelihood: number; // 1-5
  count: number;
  risks?: Array<{ id: string; name: string }>;
}

interface RiskHeatMapProps {
  data: RiskCell[];
  onCellClick?: (cell: RiskCell) => void;
  showLabels?: boolean;
  size?: "sm" | "md" | "lg";
}

const impactLabels = ["Very Low", "Low", "Medium", "High", "Very High"];
const likelihoodLabels = ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"];

const sizeClasses = {
  sm: "w-10 h-10 text-xs",
  md: "w-14 h-14 text-sm",
  lg: "w-20 h-20 text-base",
};

export function RiskHeatMap({
  data,
  onCellClick,
  showLabels = true,
  size = "md",
}: RiskHeatMapProps) {
  // Create a 5x5 matrix
  const matrix: (RiskCell | null)[][] = Array(5)
    .fill(null)
    .map(() => Array(5).fill(null));

  // Populate matrix with data
  data.forEach((cell) => {
    if (cell.impact >= 1 && cell.impact <= 5 && cell.likelihood >= 1 && cell.likelihood <= 5) {
      matrix[5 - cell.impact][cell.likelihood - 1] = cell;
    }
  });

  return (
    <div className="flex flex-col items-center">
      <div className="flex">
        {/* Y-axis label */}
        {showLabels && (
          <div className="flex flex-col justify-center items-center mr-2">
            <span
              className="text-xs text-gray-500 dark:text-gray-400 font-medium"
              style={{ writingMode: "vertical-rl", transform: "rotate(180deg)" }}
            >
              Impact
            </span>
          </div>
        )}

        {/* Y-axis values */}
        {showLabels && (
          <div className="flex flex-col justify-around pr-2">
            {impactLabels.slice().reverse().map((label, index) => (
              <div
                key={label}
                className={cn(
                  "flex items-center justify-end",
                  sizeClasses[size]
                )}
              >
                <span className="text-xs text-gray-500 dark:text-gray-400 truncate max-w-16">
                  {label}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Matrix grid */}
        <div className="flex flex-col gap-1">
          {matrix.map((row, rowIndex) => (
            <div key={rowIndex} className="flex gap-1">
              {row.map((cell, colIndex) => {
                const impact = 5 - rowIndex;
                const likelihood = colIndex + 1;
                const bgColor = getRiskColor(impact, likelihood);
                const riskLevel = getRiskLevel(impact, likelihood);
                const count = cell?.count ?? 0;

                return (
                  <button
                    key={`${rowIndex}-${colIndex}`}
                    onClick={() =>
                      onCellClick?.({
                        impact,
                        likelihood,
                        count,
                        risks: cell?.risks,
                      })
                    }
                    className={cn(
                      sizeClasses[size],
                      "rounded-md flex items-center justify-center font-semibold",
                      "transition-all hover:scale-105 hover:shadow-lg",
                      "border border-white/20 dark:border-black/20",
                      onCellClick && "cursor-pointer",
                      !onCellClick && "cursor-default"
                    )}
                    style={{
                      backgroundColor: bgColor,
                      opacity: count > 0 ? 1 : 0.4,
                    }}
                    title={`Impact: ${impactLabels[impact - 1]}, Likelihood: ${likelihoodLabels[likelihood - 1]}, Count: ${count}`}
                  >
                    <span
                      className={cn(
                        "text-white drop-shadow-sm",
                        count === 0 && "opacity-50"
                      )}
                    >
                      {count}
                    </span>
                  </button>
                );
              })}
            </div>
          ))}

          {/* X-axis values */}
          {showLabels && (
            <div className="flex gap-1 mt-2">
              {likelihoodLabels.map((label) => (
                <div
                  key={label}
                  className={cn(
                    "flex items-start justify-center",
                    sizeClasses[size]
                  )}
                >
                  <span className="text-xs text-gray-500 dark:text-gray-400 text-center truncate">
                    {label.split(" ")[0]}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* X-axis label */}
      {showLabels && (
        <div className="mt-2">
          <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">
            Likelihood
          </span>
        </div>
      )}

      {/* Legend */}
      <div className="flex items-center gap-4 mt-4">
        <div className="flex items-center gap-2">
          {[1, 2, 3, 4, 5].map((level) => (
            <div key={level} className="flex items-center gap-1">
              <div
                className="w-4 h-4 rounded"
                style={{ backgroundColor: getRiskColor(level, level) }}
              />
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {level === 1 && "Low"}
                {level === 3 && "Medium"}
                {level === 5 && "Critical"}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Mini version for dashboard cards
export function RiskHeatMapMini({ data }: { data: RiskCell[] }) {
  return (
    <RiskHeatMap data={data} showLabels={false} size="sm" />
  );
}
