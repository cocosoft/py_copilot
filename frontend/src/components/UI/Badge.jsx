import React, { memo, useMemo } from 'react';
import { motion } from 'framer-motion';
import classNames from 'classnames';
import PropTypes from 'prop-types';

const Badge = memo(({
  children,
  variant = 'default',
  size = 'medium',
  color,
  dot = false,
  count,
  maxCount = 99,
  showZero = false,
  className,
  ...props
}) => {
  const variantClasses = useMemo(() => ({
    default: [
      'bg-gray-100',
      'text-gray-800',
      'border-gray-200',
    ],
    primary: [
      'bg-blue-100',
      'text-blue-800',
      'border-blue-200',
    ],
    success: [
      'bg-green-100',
      'text-green-800',
      'border-green-200',
    ],
    warning: [
      'bg-yellow-100',
      'text-yellow-800',
      'border-yellow-200',
    ],
    danger: [
      'bg-red-100',
      'text-red-800',
      'border-red-200',
    ],
    info: [
      'bg-cyan-100',
      'text-cyan-800',
      'border-cyan-200',
    ],
  }), []);

  const sizeClasses = useMemo(() => ({
    small: ['px-2', 'py-0.5', 'text-xs', 'min-w-[1rem]', 'h-4'],
    medium: ['px-2.5', 'py-0.5', 'text-sm', 'min-w-[1.25rem]', 'h-5'],
    large: ['px-3', 'py-1', 'text-sm', 'min-w-[1.5rem]', 'h-6'],
  }), []);

  const dotSizes = useMemo(() => ({
    small: 'w-1.5 h-1.5',
    medium: 'w-2 h-2',
    large: 'w-2.5 h-2.5',
  }), []);

  const displayCount = useMemo(() => {
    if (count === undefined) return null;
    if (!showZero && count === 0) return null;
    return count > maxCount ? `${maxCount}+` : count;
  }, [count, maxCount, showZero]);

  const badgeClasses = useMemo(() => classNames(
    'inline-flex',
    'items-center',
    'justify-center',
    'font-medium',
    'rounded-full',
    'border',
    variantClasses[variant],
    sizeClasses[size],
    className
  ), [variantClasses, variant, sizeClasses, size, className]);

  const dotClass = useMemo(() => {
    if (!dot) return null;
    return classNames(
      'rounded-full',
      'mr-1',
      dotSizes[size],
      variantClasses[variant].find(cls => cls.includes('text-'))?.replace('text-', 'bg-')
    );
  }, [dot, dotSizes, size, variantClasses, variant]);

  if (count !== undefined) {
    if (!showZero && count === 0) return null;
    
    return (
      <motion.span
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        className={badgeClasses}
        {...props}
      >
        {dot && <span className={dotClass} />}
        {displayCount}
      </motion.span>
    );
  }

  return (
    <motion.span
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      className={badgeClasses}
      {...props}
    >
      {dot && <span className={dotClass} />}
      {children}
    </motion.span>
  );
});

Badge.propTypes = {
  children: PropTypes.node,
  variant: PropTypes.oneOf(['default', 'primary', 'success', 'warning', 'danger', 'info']),
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  color: PropTypes.string,
  dot: PropTypes.bool,
  count: PropTypes.number,
  maxCount: PropTypes.number,
  showZero: PropTypes.bool,
  className: PropTypes.string,
};

export default Badge;