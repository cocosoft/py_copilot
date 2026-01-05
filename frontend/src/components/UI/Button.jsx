import React from 'react';
import { motion } from 'framer-motion';
import classNames from 'classnames';
import PropTypes from 'prop-types';

const Button = ({
  children,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
  icon,
  iconPosition = 'left',
  fullWidth = false,
  className,
  onClick,
  type = 'button',
  ...props
}) => {
  const baseClasses = [
    'inline-flex',
    'items-center',
    'justify-center',
    'font-medium',
    'rounded-lg',
    'transition-all',
    'duration-200',
    'focus:outline-none',
    'focus:ring-2',
    'focus:ring-offset-2',
    'disabled:opacity-50',
    'disabled:cursor-not-allowed',
    'disabled:transform-none',
  ];

  const variantClasses = {
    primary: [
      'bg-blue-600',
      'text-white',
      'hover:bg-blue-700',
      'active:bg-blue-800',
      'focus:ring-blue-500',
      'shadow-sm',
      'hover:shadow-md',
    ],
    secondary: [
      'bg-gray-200',
      'text-gray-900',
      'hover:bg-gray-300',
      'active:bg-gray-400',
      'focus:ring-gray-500',
    ],
    outline: [
      'bg-transparent',
      'border-2',
      'border-blue-600',
      'text-blue-600',
      'hover:bg-blue-600',
      'hover:text-white',
      'active:bg-blue-700',
      'active:border-blue-700',
      'focus:ring-blue-500',
    ],
    ghost: [
      'bg-transparent',
      'text-gray-700',
      'hover:bg-gray-100',
      'active:bg-gray-200',
      'focus:ring-gray-500',
    ],
    danger: [
      'bg-red-600',
      'text-white',
      'hover:bg-red-700',
      'active:bg-red-800',
      'focus:ring-red-500',
      'shadow-sm',
      'hover:shadow-md',
    ],
  };

  const sizeClasses = {
    small: ['px-3', 'py-1.5', 'text-sm', 'gap-1.5'],
    medium: ['px-4', 'py-2', 'text-sm', 'gap-2'],
    large: ['px-6', 'py-3', 'text-base', 'gap-2.5'],
  };

  const widthClasses = fullWidth ? ['w-full'] : [];

  const allClasses = [
    ...baseClasses,
    ...variantClasses[variant],
    ...sizeClasses[size],
    ...widthClasses,
    className,
  ].filter(Boolean);

  const handleClick = (e) => {
    if (!disabled && !loading && onClick) {
      onClick(e);
    }
  };

  return (
    <motion.button
      whileHover={!disabled && !loading ? { scale: 1.02 } : {}}
      whileTap={!disabled && !loading ? { scale: 0.98 } : {}}
      className={classNames(...allClasses)}
      onClick={handleClick}
      disabled={disabled || loading}
      type={type}
      {...props}
    >
      {loading ? (
        <svg
          className={classNames(
            'animate-spin',
            size === 'small' ? 'w-3 h-3' : size === 'large' ? 'w-5 h-5' : 'w-4 h-4'
          )}
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      ) : (
        <>
          {icon && iconPosition === 'left' && (
            <span className={classNames(
              size === 'small' ? 'w-3 h-3' : size === 'large' ? 'w-5 h-5' : 'w-4 h-4'
            )}>
              {icon}
            </span>
          )}
          {children && <span>{children}</span>}
          {icon && iconPosition === 'right' && (
            <span className={classNames(
              size === 'small' ? 'w-3 h-3' : size === 'large' ? 'w-5 h-5' : 'w-4 h-4'
            )}>
              {icon}
            </span>
          )}
        </>
      )}
    </motion.button>
  );
};

Button.propTypes = {
  children: PropTypes.node,
  variant: PropTypes.oneOf(['primary', 'secondary', 'outline', 'ghost', 'danger']),
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  disabled: PropTypes.bool,
  loading: PropTypes.bool,
  icon: PropTypes.node,
  iconPosition: PropTypes.oneOf(['left', 'right']),
  fullWidth: PropTypes.bool,
  className: PropTypes.string,
  onClick: PropTypes.func,
  type: PropTypes.string,
};

export default Button;