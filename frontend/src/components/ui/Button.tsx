import React from 'react';
import { cn } from '../../utils/cn';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      isLoading = false,
      leftIcon,
      rightIcon,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const variants = {
      primary:
        'bg-[#203A32] text-white hover:bg-[#172D28] active:bg-[#101F1C] border border-[#203A32] shadow-xs',
      secondary:
        'bg-[#DCE5D8] text-[#172D28] hover:bg-[#A8B9A3] active:bg-[#8F9E8B] border border-transparent',
      outline:
        'bg-white text-[#203A32] border border-[#A8B9A3] hover:bg-[#F5F7F2] active:bg-[#EAEFE6]',
      ghost:
        'bg-transparent text-[#203A32] hover:bg-[#EAEFE6] active:bg-[#DCE5D8]',
      danger:
        'bg-red-700 text-white hover:bg-red-800 active:bg-red-900 border border-transparent shadow-xs',
    };

    const sizes = {
      sm: 'px-2.5 py-1.5 text-xs font-medium rounded-md gap-1.5',
      md: 'px-4 py-2 text-sm font-medium rounded-lg gap-2',
      lg: 'px-5 py-2.5 text-base font-medium rounded-lg gap-2.5',
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          'inline-flex items-center justify-center transition-colors duration-150 select-none cursor-pointer focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#203A32] disabled:opacity-50 disabled:cursor-not-allowed',
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 animate-spin text-current" />
        ) : (
          leftIcon
        )}
        <span>{children}</span>
        {!isLoading && rightIcon}
      </button>
    );
  }
);

Button.displayName = 'Button';
