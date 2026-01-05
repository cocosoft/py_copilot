import React, { forwardRef } from 'react';
import { motion } from 'framer-motion';
import classNames from 'classnames';
import PropTypes from 'prop-types';

const Input = forwardRef(({
  type = 'text',
  placeholder,
  value,
  defaultValue,
  onChange,
  onFocus,
  onBlur,
  disabled = false,
  error = false,
  success = false,
  icon,
  iconPosition = 'left',
  addon,
  addonPosition = 'left',
  size = 'medium',
  fullWidth = false,
  className,
  label,
  helperText,
  required = false,
  ...props
}, ref) => {
  const sizeClasses = {
    small: ['px-3', 'py-1.5', 'text-sm'],
    medium: ['px-4', 'py-2', 'text-sm'],
    large: ['px-4', 'py-3', 'text-base'],
  };

  const stateClasses = [
    'transition-all',
    'duration-200',
    'border',
    'rounded-lg',
    'focus:outline-none',
    'focus:ring-2',
    'focus:ring-offset-1',
    'disabled:bg-gray-50',
    'disabled:text-gray-500',
    'disabled:cursor-not-allowed',
  ];

  let statusClasses = [];

  if (error) {
    statusClasses = [
      'border-red-300',
      'focus:border-red-500',
      'focus:ring-red-500',
      'text-red-900',
      'placeholder-red-300',
    ];
  } else if (success) {
    statusClasses = [
      'border-green-300',
      'focus:border-green-500',
      'focus:ring-green-500',
      'text-green-900',
    ];
  } else {
    statusClasses = [
      'border-gray-300',
      'focus:border-blue-500',
      'focus:ring-blue-500',
      'text-gray-900',
      'placeholder-gray-400',
    ];
  }

  const iconClasses = iconPosition === 'left' ? ['pl-10'] : ['pr-10'];

  const inputContainerClasses = [
    'relative',
    fullWidth ? 'w-full' : '',
  ].filter(Boolean);

  const addonClasses = [
    'inline-flex',
    'items-center',
    'px-3',
    'text-sm',
    'text-gray-700',
    'bg-gray-50',
    'border',
    'border-r-0',
    'border-gray-300',
    'rounded-l-lg',
    'select-none',
  ];

  const allInputClasses = [
    ...stateClasses,
    ...statusClasses,
    ...sizeClasses[size],
    ...(icon ? iconClasses : []),
    ...(addon && addonPosition === 'left' ? ['rounded-r-lg'] : []),
    ...(addon && addonPosition === 'right' ? ['rounded-l-lg'] : []),
    'bg-white',
    className,
  ].filter(Boolean);

  const inputElement = (
    <div className={inputContainerClasses.join(' ')}>
      {addon && addonPosition === 'left' && (
        <div className={addonClasses.join(' ')}>
          {addon}
        </div>
      )}
      
      <div className="relative">
        {icon && (
          <div className={classNames(
            'absolute',
            'inset-y-0',
            'flex',
            'items-center',
            iconPosition === 'left' ? 'left-0 pl-3' : 'right-0 pr-3',
            'pointer-events-none'
          )}>
            <div className={classNames(
              'text-gray-400',
              size === 'small' ? 'w-4 h-4' : size === 'large' ? 'w-5 h-5' : 'w-4 h-4'
            )}>
              {icon}
            </div>
          </div>
        )}
        
        <input
          ref={ref}
          type={type}
          value={value}
          defaultValue={defaultValue}
          onChange={onChange}
          onFocus={onFocus}
          onBlur={onBlur}
          disabled={disabled}
          placeholder={placeholder}
          className={allInputClasses.join(' ')}
          {...props}
        />
      </div>
      
      {addon && addonPosition === 'right' && (
        <div className={addonClasses.join(' ')}>
          {addon}
        </div>
      )}
    </div>
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={fullWidth ? 'w-full' : ''}
    >
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      
      {inputElement}
      
      {helperText && (
        <p className={classNames(
          'mt-1',
          'text-sm',
          error ? 'text-red-600' : success ? 'text-green-600' : 'text-gray-500'
        )}>
          {helperText}
        </p>
      )}
    </motion.div>
  );
});

Input.displayName = 'Input';

Input.propTypes = {
  type: PropTypes.string,
  placeholder: PropTypes.string,
  value: PropTypes.string,
  defaultValue: PropTypes.string,
  onChange: PropTypes.func,
  onFocus: PropTypes.func,
  onBlur: PropTypes.func,
  disabled: PropTypes.bool,
  error: PropTypes.bool,
  success: PropTypes.bool,
  icon: PropTypes.node,
  iconPosition: PropTypes.oneOf(['left', 'right']),
  addon: PropTypes.node,
  addonPosition: PropTypes.oneOf(['left', 'right']),
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  fullWidth: PropTypes.bool,
  className: PropTypes.string,
  label: PropTypes.string,
  helperText: PropTypes.string,
  required: PropTypes.bool,
};

export default Input;