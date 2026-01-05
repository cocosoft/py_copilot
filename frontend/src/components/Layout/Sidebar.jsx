import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import classNames from 'classnames';
import PropTypes from 'prop-types';

const Sidebar = ({
  children,
  width = 240,
  collapsedWidth = 64,
  collapsed = false,
  position = 'left',
  theme = 'light',
  className,
  ...props
}) => {
  const [hovered, setHovered] = useState(false);

  const themeClasses = {
    light: 'bg-white border-gray-200 text-gray-900',
    dark: 'bg-gray-900 border-gray-700 text-white',
  };

  const positionClasses = position === 'left' ? 'left-0' : 'right-0';

  return (
    <motion.div
      className={classNames(
        'fixed top-0 bottom-0 z-40 border-r',
        positionClasses,
        themeClasses[theme],
        className
      )}
      style={{
        width: collapsed && !hovered ? collapsedWidth : width,
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      animate={{
        width: collapsed && !hovered ? collapsedWidth : width,
      }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
      {...props}
    >
      <div className="flex flex-col h-full">
        {children}
      </div>
    </motion.div>
  );
};

Sidebar.propTypes = {
  children: PropTypes.node,
  width: PropTypes.number,
  collapsedWidth: PropTypes.number,
  collapsed: PropTypes.bool,
  position: PropTypes.oneOf(['left', 'right']),
  theme: PropTypes.oneOf(['light', 'dark']),
  className: PropTypes.string,
};

export default Sidebar;