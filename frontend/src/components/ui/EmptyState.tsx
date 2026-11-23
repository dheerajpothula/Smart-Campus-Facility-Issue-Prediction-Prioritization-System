import React from 'react';
import { cn } from '../../utils/cn';
import { Inbox } from 'lucide-react';

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  className,
}) => {
  return (
    <div className={cn('flex flex-col items-center justify-center p-8 text-center rounded-xl border border-dashed border-[#A8B9A3] bg-[#F5F7F2]/40', className)}>
      <div className="w-12 h-12 rounded-full bg-[#DCE5D8] flex items-center justify-center text-[#203A32] mb-3">
        {icon || <Inbox className="w-6 h-6" />}
      </div>
      <h4 className="text-sm font-semibold text-[#172D28]">{title}</h4>
      {description && <p className="text-xs text-[#52605B] max-w-sm mt-1">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
};
