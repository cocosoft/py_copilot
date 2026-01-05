import React from 'react';
import { motion } from 'framer-motion';
import classNames from 'classnames';
import PropTypes from 'prop-types';

const Card = ({
  children,
  title,
  subtitle,
  extra,
  className,
  headerClassName,
  bodyClassName,
  footer,
  padding = 'default',
  hover = false,
  shadow = 'default',
  ...props
}) => {
  const paddingClasses = {
    none: '',
    small: 'p-4',
    default: 'p-6',
    large: 'p-8',
  };

  const shadowClasses = {
    none: '',
    small: 'shadow-sm',
    default: 'shadow-md',
    large: 'shadow-lg',
    xl: 'shadow-xl',
  };

  const CardComponent = hover ? motion.div : 'div';

  return (
    <CardComponent
      className={classNames(
        'bg-white rounded-xl border border-gray-200',
        shadowClasses[shadow],
        className
      )}
      {...(hover && {
        whileHover: { y: -2, boxShadow: '0 10px 25px -3px rgba(0, 0, 0, 0.1)' },
        transition: { duration: 0.2 }
      })}
      {...props}
    >
      {(title || subtitle || extra || footer) && (
        <div className={classNames(
          'border-b border-gray-200',
          headerClassName,
          paddingClasses[padding]
        )}>
          <div className="flex items-center justify-between">
            <div>
              {title && (
                <h3 className="text-lg font-semibold text-gray-900">
                  {title}
                </h3>
              )}
              {subtitle && (
                <p className="text-sm text-gray-600 mt-1">
                  {subtitle}
                </p>
              )}
            </div>
            {extra && (
              <div className="flex-shrink-0">
                {extra}
              </div>
            )}
          </div>
        </div>
      )}

      {children && (
        <div className={classNames(
          paddingClasses[padding],
          bodyClassName
        )}>
          {children}
        </div>
      )}

      {footer && (
        <div className={classNames(
          'border-t border-gray-200',
          headerClassName,
          paddingClasses[padding]
        )}>
          {footer}
        </div>
      )}
    </CardComponent>
  );
};

Card.propTypes = {
  children: PropTypes.node,
  title: PropTypes.string,
  subtitle: PropTypes.string,
  extra: PropTypes.node,
  className: PropTypes.string,
  headerClassName: PropTypes.string,
  bodyClassName: PropTypes.string,
  footer: PropTypes.node,
  padding: PropTypes.oneOf(['none', 'small', 'default', 'large']),
  hover: PropTypes.bool,
  shadow: PropTypes.oneOf(['none', 'small', 'default', 'large', 'xl']),
};

export default Card;