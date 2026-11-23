import React from 'react';
import { cn } from '../../utils/cn';
import { getStatusBadgeVariant, getPriorityBadgeVariant } from '../../utils/formatters';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'forest' | 'sage' | 'outline';
  status?: string;
  priority?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = 'default',
  status,
  priority,
  children,
  ...props
}) => {
  if (status) {
    const s = getStatusBadgeVariant(status);
    return (
      <span
        className={cn(
          'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border',
          s.bg,
          s.text,
          s.border,
          className
        )}
        {...props}
      >
        <span className={cn('w-1.5 h-1.5 rounded-full', s.dot)} />
        {children || status}
      </span>
    );
  }

  if (priority) {
    const p = getPriorityBadgeVariant(priority);
    return (
      <span
        className={cn(
          'inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border',
          p.bg,
          p.text,
          p.border,
          className
        )}
        {...props}
      >
        {children || priority}
      </span>
    );
  }

  const variants = {
    default: 'bg-[#F5F7F2] text-[#172D28] border-[#DCE5D8]',
    forest: 'bg-[#203A32] text-white border-[#203A32]',
    sage: 'bg-[#DCE5D8] text-[#172D28] border-[#A8B9A3]',
    outline: 'bg-transparent text-[#203A32] border-[#203A32]',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border',
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
};
