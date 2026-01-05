import { render, screen, fireEvent } from '@testing-library/react';
import { act } from 'react-dom/test-utils';
import React from 'react';
import rootStore, { StoreProvider, StoreMonitor } from '../../stores/rootStore';

describe('Root Store Management', () => {
  beforeEach(() => {
    // 重置所有 store 状态
    act(() => {
      rootStore.reset();
    });
  });

  describe('Store Provider', () => {
    it('provides store context to child components', () => {
      const TestComponent = () => {
        const store = React.useContext(rootStore.storeContext);
        return <div>Store available: {!!store}</div>;
      };

      render(
        <StoreProvider>
          <TestComponent />
        </StoreProvider>
      );

      expect(screen.getByText('Store available: true')).toBeInTheDocument();
    });

    it('initializes all sub-stores', () => {
      const TestComponent = () => {
        const store = React.useContext(rootStore.storeContext);
        return (
          <div>
            <div>API Store: {!!store.apiStore}</div>
            <div>Auth Store: {!!store.authStore}</div>
            <div>Model Store: {!!store.modelStore}</div>
            <div>App Store: {!!store.appStore}</div>
            <div>Supplier Store: {!!store.supplierStore}</div>
          </div>
        );
      };

      render(
        <StoreProvider>
          <TestComponent />
        </StoreProvider>
      );

      expect(screen.getByText('API Store: true')).toBeInTheDocument();
      expect(screen.getByText('Auth Store: true')).toBeInTheDocument();
      expect(screen.getByText('Model Store: true')).toBeInTheDocument();
      expect(screen.getByText('App Store: true')).toBeInTheDocument();
      expect(screen.getByText('Supplier Store: true')).toBeInTheDocument();
    });
  });

  describe('Store Monitor', () => {
    it('renders in development mode', () => {
      const originalNodeEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'development';

      const TestComponent = () => {
        const store = React.useContext(rootStore.storeContext);
        return <div>Test Component</div>;
      };

      render(
        <StoreProvider>
          <StoreMonitor />
          <TestComponent />
        </StoreProvider>
      );

      // Store Monitor 应该只在开发模式下显示
      expect(document.body.querySelector('[data-testid="store-monitor"]')).toBeTruthy();

      process.env.NODE_ENV = originalNodeEnv;
    });

    it('does not render in production mode', () => {
      const originalNodeEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'production';

      const TestComponent = () => {
        const store = React.useContext(rootStore.storeContext);
        return <div>Test Component</div>;
      };

      render(
        <StoreProvider>
          <StoreMonitor />
          <TestComponent />
        </StoreProvider>
      );

      // Store Monitor 在生产模式下不应该显示
      expect(document.body.querySelector('[data-testid="store-monitor"]')).toBeFalsy();

      process.env.NODE_ENV = originalNodeEnv;
    });
  });

  describe('Store State Management', () => {
    it('allows state updates across stores', () => {
      const TestComponent = () => {
        const store = React.useContext(rootStore.storeContext);
        const [value, setValue] = React.useState('');

        const handleUpdate = () => {
          act(() => {
            store.appStore.setTheme('dark');
            setValue(store.appStore.getState().theme);
          });
        };

        return (
          <div>
            <div>Current theme: {store.appStore.getState().theme}</div>
            <button onClick={handleUpdate}>Update Theme</button>
            <div>Updated to: {value}</div>
          </div>
        );
      };

      render(
        <StoreProvider>
          <TestComponent />
        </StoreProvider>
      );

      expect(screen.getByText('Current theme: light')).toBeInTheDocument();

      fireEvent.click(screen.getByText('Update Theme'));
      expect(screen.getByText('Updated to: dark')).toBeInTheDocument();
    });

    it('supports middleware integration', () => {
      const TestComponent = () => {
        const store = React.useContext(rootStore.storeContext);
        const [actions, setActions] = React.useState([]);

        const handleAction = () => {
          act(() => {
            store.authStore.login({ username: 'test', token: 'abc123' });
            const state = store.getState();
            setActions(state.recentActions);
          });
        };

        return (
          <div>
            <div>Actions count: {actions.length}</div>
            <button onClick={handleAction}>Trigger Action</button>
          </div>
        );
      };

      render(
        <StoreProvider>
          <TestComponent />
        </StoreProvider>
      );

      fireEvent.click(screen.getByText('Trigger Action'));
      expect(screen.getByText('Actions count: 1')).toBeInTheDocument();
    });

    it('handles persistence correctly', () => {
      const TestComponent = () => {
        const store = React.useContext(rootStore.storeContext);
        const [persisted, setPersisted] = React.useState(false);

        const handlePersist = () => {
          act(() => {
            store.modelStore.setSelectedModel('test-model');
            store.persist();
            setPersisted(true);
          });
        };

        return (
          <div>
            <div>Persisted: {persisted}</div>
            <button onClick={handlePersist}>Persist Data</button>
          </div>
        );
      };

      render(
        <StoreProvider>
          <TestComponent />
        </StoreProvider>
      );

      fireEvent.click(screen.getByText('Persist Data'));
      expect(screen.getByText('Persisted: true')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('handles store initialization errors gracefully', () => {
      // 模拟 store 初始化失败
      const originalInit = rootStore.initialize;
      rootStore.initialize = jest.fn().mockImplementation(() => {
        throw new Error('Store initialization failed');
      });

      const TestComponent = () => {
        const store = React.useContext(rootStore.storeContext);
        return <div>Store available: {!!store}</div>;
      };

      expect(() => {
        render(
          <StoreProvider>
            <TestComponent />
          </StoreProvider>
        );
      }).not.toThrow();

      // 恢复原始方法
      rootStore.initialize = originalInit;
    });

    it('handles state update errors gracefully', () => {
      const TestComponent = () => {
        const store = React.useContext(rootStore.storeContext);
        const [error, setError] = React.useState(null);

        const handleError = () => {
          try {
            act(() => {
              // 尝试无效的状态更新
              store.invalidStore.updateState({ invalid: true });
            });
          } catch (err) {
            setError(err.message);
          }
        };

        return (
          <div>
            <div>Error: {error || 'None'}</div>
            <button onClick={handleError}>Trigger Error</button>
          </div>
        );
      };

      render(
        <StoreProvider>
          <TestComponent />
        </StoreProvider>
      );

      fireEvent.click(screen.getByText('Trigger Error'));
      expect(screen.getByText(/Error:/)).toBeInTheDocument();
    });
  });

  describe('Performance Monitoring', () => {
    it('tracks performance metrics', () => {
      const TestComponent = () => {
        const store = React.useContext(rootStore.storeContext);
        const [metrics, setMetrics] = React.useState(null);

        const handleAction = () => {
          act(() => {
            store.modelStore.setSelectedModel('test-model');
            store.apiStore.fetchModels();
            const performanceData = store.getPerformanceMetrics();
            setMetrics(performanceData);
          });
        };

        return (
          <div>
            <div>Metrics: {metrics ? 'Available' : 'None'}</div>
            <button onClick={handleAction}>Track Performance</button>
          </div>
        );
      };

      render(
        <StoreProvider>
          <TestComponent />
        </StoreProvider>
      );

      fireEvent.click(screen.getByText('Track Performance'));
      expect(screen.getByText('Metrics: Available')).toBeInTheDocument();
    });

    it('provides state history tracking', () => {
      const TestComponent = () => {
        const store = React.useContext(rootStore.storeContext);
        const [history, setHistory] = React.useState([]);

        const handleHistory = () => {
          act(() => {
            store.authStore.login({ username: 'test', token: 'abc123' });
            store.appStore.setTheme('dark');
            store.appStore.setLanguage('en');
            const historyData = store.getStateHistory();
            setHistory(historyData);
          });
        };

        return (
          <div>
            <div>History entries: {history.length}</div>
            <button onClick={handleHistory}>Generate History</button>
          </div>
        );
      };

      render(
        <StoreProvider>
          <TestComponent />
        </StoreProvider>
      );

      fireEvent.click(screen.getByText('Generate History'));
      expect(screen.getByText('History entries: 3')).toBeInTheDocument();
    });
  });
});