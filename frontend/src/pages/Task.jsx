import React from 'react';
import TaskList from '../components/TaskManagement/TaskList';
import './task.css';

function Task() {
  return (
    <div className="task-page">
      <div className="task-page-container">
        <TaskList />
      </div>
    </div>
  );
}

export default Task;
