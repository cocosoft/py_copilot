import React, { useState } from 'react';
import { motion } from 'framer-motion';
import classNames from 'classnames';
import PropTypes from 'prop-types';

const Header = ({
  children,
  left,
  right,
  height = 64,
  fixed = false,
  theme = 'light',
  className,
  ...props
}) => {
  const themeClasses = {
    light: 'bg-white border-gray-200 text-gray-900 shadow-sm',
    dark: 'bg-gray-900 border-gray-700 text-white shadow-lg',
  };

  return (
    <motion.header
      className={classNames(
        'flex items-center justify-between px-6 border-b',
        fixed ? 'fixed top-0 left-0 right-0 z-30' : 'relative',
        themeClasses[theme],
        className
      )}
      style={{ height }}
      initial={{ y: -height }}
      animate={{ y: 0 }}
      transition={{ duration: 0.3 }}
      {...props}
    >
      <div className="flex items-center flex-1">
        {left}
      </div>
      
      {children && (
        <div className="flex-1 text-center">
          {children}
        </div>
      )}
      
      <div className="flex items-center gap-4">
        {right}
      </div>
    </motion.header>
  );
};

Header.propTypes = {
  children: PropTypes.node,
  left: PropTypes.node,
  right: PropTypes.node,
  height: PropTypes.number,
  fixed: PropTypes.bool,
  theme: PropTypes.oneOf(['light', 'dark']),
  className: PropTypes.string,
};

export default Header;