import React from 'react';
import { cn } from '../../utils/cn';

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
  showCount?: boolean;
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, error, helperText, showCount = false, maxLength, value, id, ...props }, ref) => {
    const textareaId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);
    const currentLength = typeof value === 'string' ? value.length : 0;

    return (
      <div className="w-full space-y-1.5">
        <div className="flex justify-between items-center">
          {label && (
            <label htmlFor={textareaId} className="block text-xs font-semibold uppercase tracking-wider text-[#172D28]">
              {label}
              {props.required && <span className="text-red-600 ml-1">*</span>}
            </label>
          )}
          {showCount && maxLength && (
            <span className={cn('text-xs font-mono', currentLength > maxLength ? 'text-red-600 font-bold' : 'text-[#52605B]')}>
              {currentLength}/{maxLength}
            </span>
          )}
        </div>
        <textarea
          ref={ref}
          id={textareaId}
          maxLength={maxLength}
          value={value}
          className={cn(
            'w-full rounded-lg border bg-white p-3 text-sm text-[#172D28] placeholder-[#A8B9A3] transition-colors resize-y min-h-[90px]',
            'focus:border-[#203A32] focus:ring-1 focus:ring-[#203A32] focus:outline-hidden',
            error
              ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
              : 'border-[#DCE5D8] hover:border-[#A8B9A3]',
            className
          )}
          {...props}
        />
        {error && <p className="text-xs text-red-600 font-medium">{error}</p>}
        {helperText && !error && <p className="text-xs text-[#52605B]">{helperText}</p>}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';
