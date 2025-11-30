const Loading = ({ message = '加载中...' }) => {
  return (
    <div className="loading">
      <div className="loading-spinner"></div>
      <div className="loading-message">{message}</div>
    </div>
  );
};

export default Loading;