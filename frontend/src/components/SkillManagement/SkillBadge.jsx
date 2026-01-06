import React from 'react';
import './SkillManagement.css';

function SkillBadge({ status, label, color = 'default' }) {
  const statusColors = {
    default: { bg: '#f3f4f6', text: '#6b7280' },
    success: { bg: '#dcfce7', text: '#16a34a' },
    warning: { bg: '#fef3c7', text: '#d97706' },
    error: { bg: '#fee2e2', text: '#dc2626' },
    info: { bg: '#dbeafe', text: '#2563eb' },
  };

  const badgeStyle = {
    backgroundColor: statusColors[color]?.bg || statusColors.default.bg,
    color: statusColors[color]?.text || statusColors.default.text,
  };

  return (
    <span className="skill-badge" style={badgeStyle}>
      {label || status}
    </span>
  );
}

export default SkillBadge;
