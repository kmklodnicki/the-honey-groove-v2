import React from 'react';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from './ui/tooltip';
import { getGradeInfo, gradeCode } from '../utils/grading';

/**
 * GradeLabel — displays "VG+ - The Sweet Spot" with a hover tooltip.
 * Props:
 *   condition: raw condition value (e.g. "VG+", "Near Mint", "Very Good Plus")
 *   variant: "pill" | "inline" | "compact"
 *   className: additional classes
 */
export const GradeLabel = ({ condition, variant = 'pill', className = '' }) => {
  const info = getGradeInfo(condition);
  const code = gradeCode(condition);

  if (!info) {
    // Fallback for unrecognized grades
    if (!condition) return null;
    return <span className={className}>{condition}</span>;
  }

  const display = (
    <>
      <span className="font-semibold">{info.code}</span>
      <span className="opacity-70 mx-1">-</span>
      <span>{info.honey} {info.emoji}</span>
    </>
  );

  const tooltipContent = (
    <div className="max-w-[300px] space-y-1">
      <p className="font-semibold text-sm">{info.code} ({info.full})</p>
      <p className="text-xs leading-relaxed opacity-90">{info.tooltip}</p>
    </div>
  );

  if (variant === 'pill') {
    return (
      <TooltipProvider delayDuration={100}>
        <Tooltip>
          <TooltipTrigger asChild>
            <span
              className={`inline-flex items-center gap-0.5 px-2.5 py-1 rounded-full text-xs border cursor-help ${info.color} ${className}`}
              data-testid="grade-label-pill"
            >
              {display}
            </span>
          </TooltipTrigger>
          <TooltipContent side="top" className="bg-vinyl-black text-white border-none shadow-xl px-4 py-3 rounded-xl">
            {tooltipContent}
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  if (variant === 'compact') {
    return (
      <TooltipProvider delayDuration={100}>
        <Tooltip>
          <TooltipTrigger asChild>
            <span
              className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-[10px] border cursor-help ${info.color} ${className}`}
              data-testid="grade-label-compact"
            >
              <span className="font-bold">{info.code}</span>
              <span className="opacity-70">{info.emoji}</span>
            </span>
          </TooltipTrigger>
          <TooltipContent side="top" className="bg-vinyl-black text-white border-none shadow-xl px-4 py-3 rounded-xl">
            {tooltipContent}
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  // inline variant
  return (
    <TooltipProvider delayDuration={100}>
      <Tooltip>
        <TooltipTrigger asChild>
          <span className={`inline-flex items-center gap-0.5 cursor-help ${className}`} data-testid="grade-label-inline">
            {display}
          </span>
        </TooltipTrigger>
        <TooltipContent side="top" className="bg-vinyl-black text-white border-none shadow-xl px-4 py-3 rounded-xl">
          {tooltipContent}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

export default GradeLabel;
