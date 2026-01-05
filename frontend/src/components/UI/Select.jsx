import React, { forwardRef, useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { createPortal } from 'react-dom';
import classNames from 'classnames';
import PropTypes from 'prop-types';

const Select = forwardRef(({
  options = [],
  value,
  defaultValue,
  onChange,
  placeholder = '请选择...',
  disabled = false,
  error = false,
  size = 'medium',
  fullWidth = false,
  className,
  label,
  helperText,
  required = false,
  searchable = false,
  multiple = false,
  clearable = false,
  loading = false,
  ...props
}, ref) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchValue, setSearchValue] = useState('');
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const selectRef = useRef(null);
  const searchRef = useRef(null);

  const displayValue = React.useMemo(() => {
    if (multiple && Array.isArray(value)) {
      if (value.length === 0) return placeholder;
      if (value.length === 1) {
        const selectedOption = options.find(opt => opt.value === value[0]);
        return selectedOption ? selectedOption.label : value[0];
      }
      return `${value.length} 个选项已选择`;
    } else {
      const selectedOption = options.find(opt => opt.value === value);
      return selectedOption ? selectedOption.label : placeholder;
    }
  }, [value, options, placeholder, multiple]);

  const filteredOptions = React.useMemo(() => {
    if (!searchable || !searchValue) return options;
    return options.filter(opt => 
      opt.label.toLowerCase().includes(searchValue.toLowerCase()) ||
      opt.value.toString().toLowerCase().includes(searchValue.toLowerCase())
    );
  }, [options, searchValue, searchable]);

  useEffect(() => {
    if (isOpen && searchable && searchRef.current) {
      searchRef.current.focus();
    }
  }, [isOpen, searchable]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (selectRef.current && !selectRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    const handleKeyDown = (event) => {
      if (!isOpen) return;

      switch (event.key) {
        case 'Escape':
          setIsOpen(false);
          selectRef.current?.focus();
          break;
        case 'ArrowDown':
          event.preventDefault();
          setFocusedIndex(prev => 
            prev < filteredOptions.length - 1 ? prev + 1 : prev
          );
          break;
        case 'ArrowUp':
          event.preventDefault();
          setFocusedIndex(prev => prev > 0 ? prev - 1 : -1);
          break;
        case 'Enter':
        case ' ':
          event.preventDefault();
          if (focusedIndex >= 0) {
            handleSelect(filteredOptions[focusedIndex]);
          }
          break;
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, focusedIndex, filteredOptions]);

  const sizeClasses = {
    small: ['px-3', 'py-1.5', 'text-sm'],
    medium: ['px-4', 'py-2', 'text-sm'],
    large: ['px-4', 'py-3', 'text-base'],
  };

  const stateClasses = [
    'w-full',
    'text-left',
    'bg-white',
    'border',
    'rounded-lg',
    'transition-all',
    'duration-200',
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
    ];
  } else {
    statusClasses = [
      'border-gray-300',
      'focus:border-blue-500',
      'focus:ring-blue-500',
    ];
  }

  const allClasses = [
    ...stateClasses,
    ...statusClasses,
    ...sizeClasses[size],
    isOpen ? 'ring-2 ring-blue-500 ring-offset-1' : '',
    className,
  ].filter(Boolean);

  const handleToggle = () => {
    if (!disabled && !loading) {
      setIsOpen(!isOpen);
      if (!isOpen) {
        setFocusedIndex(-1);
      }
    }
  };

  const handleSelect = (option) => {
    if (multiple) {
      const currentValues = Array.isArray(value) ? value : [];
      const newValues = currentValues.includes(option.value)
        ? currentValues.filter(v => v !== option.value)
        : [...currentValues, option.value];
      onChange?.(newValues);
    } else {
      onChange?.(option.value);
      setIsOpen(false);
    }
    setSearchValue('');
  };

  const handleClear = (e) => {
    e.stopPropagation();
    if (multiple) {
      onChange?.([]);
    } else {
      onChange?.('');
    }
  };

  const isSelected = (optionValue) => {
    if (multiple) {
      return Array.isArray(value) && value.includes(optionValue);
    }
    return value === optionValue;
  };

  const selectContent = (
    <div ref={selectRef} className="relative">
      <button
        ref={ref}
        type="button"
        className={allClasses.join(' ')}
        onClick={handleToggle}
        disabled={disabled || loading}
        {...props}
      >
        <div className="flex items-center justify-between">
          <span className={classNames(
            'truncate',
            displayValue === placeholder ? 'text-gray-500' : 'text-gray-900'
          )}>
            {loading ? (
              <div className="flex items-center gap-2">
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                加载中...
              </div>
            ) : (
              displayValue
            )}
          </span>
          
          <div className="flex items-center gap-1">
            {clearable && !loading && ((multiple && Array.isArray(value) && value.length > 0) || (!multiple && value)) && (
              <button
                type="button"
                onClick={handleClear}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <svg className="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
            
            <svg 
              className={classNames(
                'w-4 h-4 text-gray-400 transition-transform duration-200',
                isOpen ? 'transform rotate-180' : ''
              )} 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-hidden"
          >
            {searchable && (
              <div className="p-2 border-b border-gray-200">
                <input
                  ref={searchRef}
                  type="text"
                  value={searchValue}
                  onChange={(e) => setSearchValue(e.target.value)}
                  placeholder="搜索..."
                  className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            )}
            
            <div className="max-h-48 overflow-y-auto">
              {filteredOptions.length === 0 ? (
                <div className="px-3 py-2 text-sm text-gray-500 text-center">
                  {searchable && searchValue ? '未找到匹配选项' : '暂无选项'}
                </div>
              ) : (
                filteredOptions.map((option, index) => (
                  <button
                    key={option.value}
                    type="button"
                    className={classNames(
                      'w-full px-3 py-2 text-left text-sm hover:bg-gray-50 focus:bg-gray-50 focus:outline-none',
                      focusedIndex === index ? 'bg-blue-50 text-blue-700' : 'text-gray-900',
                      isSelected(option.value) ? 'bg-blue-100 text-blue-700 font-medium' : ''
                    )}
                    onClick={() => handleSelect(option)}
                  >
                    <div className="flex items-center justify-between">
                      <span className="truncate">{option.label}</span>
                      {isSelected(option.value) && (
                        <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                    </div>
                  </button>
                ))
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );

  return (
    <div className={fullWidth ? 'w-full' : ''}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      
      {selectContent}
      
      {helperText && (
        <p className={classNames(
          'mt-1',
          'text-sm',
          error ? 'text-red-600' : 'text-gray-500'
        )}>
          {helperText}
        </p>
      )}
    </div>
  );
});

Select.displayName = 'Select';

Select.propTypes = {
  options: PropTypes.arrayOf(PropTypes.shape({
    value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    label: PropTypes.string,
    disabled: PropTypes.bool,
  })),
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number, PropTypes.array]),
  defaultValue: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  onChange: PropTypes.func,
  placeholder: PropTypes.string,
  disabled: PropTypes.bool,
  error: PropTypes.bool,
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  fullWidth: PropTypes.bool,
  className: PropTypes.string,
  label: PropTypes.string,
  helperText: PropTypes.string,
  required: PropTypes.bool,
  searchable: PropTypes.bool,
  multiple: PropTypes.bool,
  clearable: PropTypes.bool,
  loading: PropTypes.bool,
};

export default Select;