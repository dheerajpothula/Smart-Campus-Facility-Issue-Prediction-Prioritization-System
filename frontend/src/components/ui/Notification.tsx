import React from 'react';
import { cn } from '../../utils/cn';
import { CheckCircle2, AlertTriangle, AlertCircle, Info, X } from 'lucide-react';

export interface NotificationProps {
  type?: 'success' | 'warning' | 'error' | 'info';
  title?: string;
  message: string;
  onClose?: () => void;
  className?: string;
}

export const Notification: React.FC<NotificationProps> = ({
  type = 'info',
  title,
  message,
  onClose,
  className,
}) => {
  const styles = {
    success: {
      bg: 'bg-emerald-50 border-emerald-200 text-emerald-900',
      icon: <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />,
    },
    warning: {
      bg: 'bg-amber-50 border-amber-200 text-amber-900',
      icon: <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />,
    },
    error: {
      bg: 'bg-red-50 border-red-200 text-red-900',
      icon: <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />,
    },
    info: {
      bg: 'bg-[#F0F4EE] border-[#DCE5D8] text-[#172D28]',
      icon: <Info className="w-5 h-5 text-[#203A32] shrink-0" />,
    },
  };

  const current = styles[type];

  return (
    <div className={cn('flex items-start gap-3 p-3.5 rounded-xl border text-sm', current.bg, className)}>
      {current.icon}
      <div className="flex-1">
        {title && <h5 className="font-semibold text-xs uppercase tracking-wider mb-0.5">{title}</h5>}
        <p className="text-xs leading-relaxed">{message}</p>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="p-1 rounded-md opacity-70 hover:opacity-100 transition-opacity"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};
