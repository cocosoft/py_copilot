const Error = ({ message, onRetry }) => {
  return (
    <div className="error">
      <div className="error-message">{message}</div>
      {onRetry && (
        <button className="btn btn-primary" onClick={onRetry}>
          重试
        </button>
      )}
    </div>
  );
};

export default Error;