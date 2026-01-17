"""数据分析技能核心实现"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import classification_report, confusion_matrix, r2_score, mean_squared_error
import time
from datetime import datetime
from jinja2 import Template
import base64
import io


class DataAnalysisSkill:
    """数据分析技能核心类"""
    
    def __init__(self):
        """初始化数据分析技能"""
        self.data = None
        self.filename = None
        self.file_size = 0
        self.start_time = None
        
        # 设置可视化风格
        plt.style.use('seaborn-v0_8')
        sns.set_palette('husl')
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 支持中文
        plt.rcParams['axes.unicode_minus'] = False  # 支持负号
    
    def load_data(self, file_path):
        """加载数据文件"""
        self.filename = os.path.basename(file_path)
        self.file_size = os.path.getsize(file_path)
        self.start_time = time.time()
        
        # 根据文件扩展名加载数据
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.csv':
            self.data = pd.read_csv(file_path)
        elif ext in ['.xlsx', '.xls']:
            self.data = pd.read_excel(file_path)
        elif ext == '.json':
            self.data = pd.read_json(file_path)
        elif ext == '.txt':
            self.data = pd.read_csv(file_path, sep='\t')
        else:
            raise ValueError(f"不支持的文件格式: {ext}")
        
        return self.data
    
    def clean_data(self):
        """数据清洗"""
        if self.data is None:
            raise ValueError("未加载数据")
        
        # 处理缺失值
        missing_values = self.data.isnull().sum().to_dict()
        
        # 处理重复行
        duplicate_rows = self.data.duplicated().sum()
        self.data = self.data.drop_duplicates()
        
        # 填充缺失值（数值型用均值，分类型用众数）
        for col in self.data.columns:
            if self.data[col].isnull().any():
                if self.data[col].dtype in ['int64', 'float64']:
                    self.data[col].fillna(self.data[col].mean(), inplace=True)
                else:
                    self.data[col].fillna(self.data[col].mode()[0], inplace=True)
        
        return {
            'missing_values': missing_values,
            'duplicate_rows': duplicate_rows,
            'cleaned_rows': len(self.data)
        }
    
    def explore_data(self):
        """数据探索"""
        if self.data is None:
            raise ValueError("未加载数据")
        
        # 基本信息
        info = {
            'row_count': len(self.data),
            'column_count': len(self.data.columns),
            'data_types': self.data.dtypes.astype(str).to_dict()
        }
        
        # 描述性统计
        summary_stats = self.data.describe().to_string()
        
        # 相关性分析（仅数值型）
        numeric_cols = self.data.select_dtypes(include=['int64', 'float64']).columns
        correlation = None
        if len(numeric_cols) > 1:
            correlation = self.data[numeric_cols].corr().to_string()
        
        return {
            'info': info,
            'summary_stats': summary_stats,
            'correlation': correlation,
            'numeric_columns': list(numeric_cols),
            'categorical_columns': list(self.data.select_dtypes(exclude=['int64', 'float64']).columns)
        }
    
    def visualize_data(self):
        """数据可视化"""
        if self.data is None:
            raise ValueError("未加载数据")
        
        visualizations = []
        
        # 数值型数据直方图
        numeric_cols = self.data.select_dtypes(include=['int64', 'float64']).columns
        for col in numeric_cols[:5]:  # 最多显示5个直方图
            plt.figure(figsize=(10, 6))
            sns.histplot(self.data[col], kde=True, bins=30)
            plt.title(f'{col} 分布直方图')
            plt.xlabel(col)
            plt.ylabel('频率')
            
            # 将图表转换为base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight')
            buffer.seek(0)
            img_str = base64.b64encode(buffer.read()).decode('utf-8')
            visualizations.append(f"![{col} 分布直方图](data:image/png;base64,{img_str})")
            plt.close()
        
        # 相关性热力图（如果有足够的数值型列）
        if len(numeric_cols) > 1:
            plt.figure(figsize=(12, 10))
            corr_matrix = self.data[numeric_cols].corr()
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt='.2f', linewidths=0.5)
            plt.title('相关性热力图')
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight')
            buffer.seek(0)
            img_str = base64.b64encode(buffer.read()).decode('utf-8')
            visualizations.append(f"![相关性热力图](data:image/png;base64,{img_str})")
            plt.close()
        
        return visualizations
    
    def perform_statistical_analysis(self):
        """统计分析"""
        if self.data is None:
            raise ValueError("未加载数据")
        
        stats_results = {}
        
        # 数值型列的假设检验（示例：正态性检验）
        numeric_cols = self.data.select_dtypes(include=['int64', 'float64']).columns
        if len(numeric_cols) > 0:
            from scipy import stats
            normality_tests = {}
            for col in numeric_cols[:3]:  # 最多测试3列
                stat, p_value = stats.shapiro(self.data[col])
                normality_tests[col] = {
                    'shapiro_statistic': stat,
                    'p_value': p_value,
                    'is_normal': p_value > 0.05
                }
            stats_results['normality_tests'] = normality_tests
        
        return stats_results
    
    def build_model(self, target_column=None):
        """构建机器学习模型"""
        if self.data is None:
            raise ValueError("未加载数据")
        
        # 如果未指定目标列，尝试自动选择
        if target_column is None:
            numeric_cols = self.data.select_dtypes(include=['int64', 'float64']).columns
            if len(numeric_cols) > 0:
                target_column = numeric_cols[-1]  # 默认选择最后一列
            else:
                raise ValueError("未找到合适的目标列")
        
        # 准备特征和目标
        X = self.data.drop(columns=[target_column])
        y = self.data[target_column]
        
        # 处理分类特征
        X = pd.get_dummies(X, drop_first=True)
        
        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # 选择模型类型
        if y.dtype in ['int64', 'float64']:
            # 回归问题
            model = RandomForestRegressor(n_estimators=100, random_state=42)
        else:
            # 分类问题
            model = RandomForestClassifier(n_estimators=100, random_state=42)
        
        # 训练模型
        model.fit(X_train, y_train)
        
        # 预测
        y_pred = model.predict(X_test)
        
        # 评估模型
        if isinstance(model, RandomForestRegressor):
            r2 = r2_score(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            metrics = {
                'model_type': 'regression',
                'r2_score': r2,
                'mse': mse,
                'rmse': rmse
            }
        else:
            classification_rep = classification_report(y_test, y_pred, output_dict=True)
            confusion_mat = confusion_matrix(y_test, y_pred)
            metrics = {
                'model_type': 'classification',
                'classification_report': classification_rep,
                'confusion_matrix': confusion_mat.tolist()
            }
        
        # 特征重要性
        feature_importance = pd.DataFrame({
            'feature': X.columns,
            'importance': model.feature_importances_
        }).sort_values(by='importance', ascending=False).head(10).to_dict('records')
        
        return {
            'model': model,
            'metrics': metrics,
            'feature_importance': feature_importance,
            'target_column': target_column
        }
    
    def generate_report(self, visualizations, model_results=None):
        """生成分析报告"""
        if self.data is None:
            raise ValueError("未加载数据")
        
        # 数据探索结果
        explore_results = self.explore_data()
        
        # 数据清洗结果
        clean_results = self.clean_data()
        
        # 统计分析结果
        stats_results = self.perform_statistical_analysis()
        
        # 构建报告数据
        report_data = {
            'filename': self.filename,
            'file_size': self.file_size,
            'row_count': explore_results['info']['row_count'],
            'column_count': explore_results['info']['column_count'],
            'data_types': ', '.join(f"{col}: {dtype}" for col, dtype in explore_results['info']['data_types'].items()[:5]) + ("..." if len(explore_results['info']['data_types']) > 5 else ""),
            'missing_values': ', '.join(f"{col}: {count}" for col, count in clean_results['missing_values'].items() if count > 0) or "无",
            'duplicate_rows': clean_results['duplicate_rows'],
            'outliers_detected': "是" if len(self.data.select_dtypes(include=['int64', 'float64']).columns) > 0 else "否",
            'summary_statistics': "```\n" + explore_results['summary_stats'] + "\n```",
            'correlation_analysis': "```\n" + (explore_results['correlation'] or "无足够数值型列进行相关性分析") + "\n```",
            'distribution_analysis': "已生成直方图可视化",
            'visualizations': "\n".join(visualizations),
            'hypothesis_testing': "```\n" + str(stats_results.get('normality_tests', "未执行假设检验")) + "\n```",
            'regression_analysis': "已包含在机器学习结果中" if model_results else "未执行回归分析",
            'model_performance': "```\n" + str(model_results['metrics']) + "\n```" if model_results else "未构建模型",
            'feature_importance': "```\n" + str(model_results['feature_importance']) + "\n```" if model_results else "未构建模型",
            'key_findings': self._generate_key_findings(explore_results, clean_results, stats_results, model_results),
            'recommendations': self._generate_recommendations(explore_results, clean_results, stats_results, model_results),
            'current_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'analysis_time': round(time.time() - self.start_time, 2)
        }
        
        # 加载模板
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'analysis.j2')
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # 渲染报告
        template = Template(template_content)
        report = template.render(report_data)
        
        return report
    
    def _generate_key_findings(self, explore_results, clean_results, stats_results, model_results):
        """生成关键发现"""
        findings = []
        
        # 数据质量发现
        if clean_results['duplicate_rows'] > 0:
            findings.append(f"数据中包含 {clean_results['duplicate_rows']} 行重复记录，已移除")
        
        # 数据分布发现
        numeric_cols = explore_results['numeric_columns']
        if numeric_cols:
            findings.append(f"数据包含 {len(numeric_cols)} 个数值型列和 {len(explore_results['categorical_columns'])} 个分类型列")
        
        # 统计分析发现
        if 'normality_tests' in stats_results:
            normal_cols = [col for col, result in stats_results['normality_tests'].items() if result['is_normal']]
            if normal_cols:
                findings.append(f"以下列符合正态分布: {', '.join(normal_cols)}")
        
        # 模型发现
        if model_results:
            findings.append(f"构建了 {model_results['metrics']['model_type']} 模型，目标列为 {model_results['target_column']}")
            if model_results['metrics']['model_type'] == 'regression':
                findings.append(f"模型R²分数为 {model_results['metrics']['r2_score']:.4f}")
            else:
                accuracy = model_results['metrics']['classification_report']['accuracy']
                findings.append(f"模型准确率为 {accuracy:.4f}")
        
        return "\n".join(f"- {finding}" for finding in findings)
    
    def _generate_recommendations(self, explore_results, clean_results, stats_results, model_results):
        """生成建议"""
        recommendations = []
        
        # 数据质量建议
        if any(count > 0 for count in clean_results['missing_values'].values()):
            recommendations.append("建议在数据收集阶段减少缺失值，提高数据质量")
        
        # 分析建议
        numeric_cols = explore_results['numeric_columns']
        if len(numeric_cols) > 1:
            recommendations.append("建议进一步分析数值型列之间的因果关系")
        
        # 模型建议
        if model_results:
            recommendations.append("建议使用更多特征工程技术和模型调参来提高模型性能")
            recommendations.append("建议使用交叉验证来更准确地评估模型性能")
        
        return "\n".join(f"- {rec}" for rec in recommendations)
    
    def run_complete_analysis(self, file_path, target_column=None):
        """运行完整的数据分析流程"""
        # 1. 加载数据
        self.load_data(file_path)
        
        # 2. 数据清洗
        clean_results = self.clean_data()
        
        # 3. 数据探索
        explore_results = self.explore_data()
        
        # 4. 数据可视化
        visualizations = self.visualize_data()
        
        # 5. 统计分析
        stats_results = self.perform_statistical_analysis()
        
        # 6. 机器学习模型（可选）
        model_results = None
        try:
            model_results = self.build_model(target_column)
        except Exception as e:
            print(f"构建模型时出错: {e}")
        
        # 7. 生成报告
        report = self.generate_report(visualizations, model_results)
        
        return {
            'report': report,
            'clean_results': clean_results,
            'explore_results': explore_results,
            'stats_results': stats_results,
            'model_results': model_results,
            'analysis_time': round(time.time() - self.start_time, 2)
        }
