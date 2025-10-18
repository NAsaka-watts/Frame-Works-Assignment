# 🦠 COVID-19 Research Analyzer

An interactive web application for analyzing and visualizing COVID-19 research publications from the CORD-19 dataset.

## 🌟 Features

- **📊 Interactive Data Analysis**: Upload and analyze CORD-19 metadata CSV files
- **📈 Temporal Trends**: Visualize publication trends over time
- **📚 Journal Analysis**: Identify top publishing journals with interactive charts
- **🔍 Source Distribution**: Analyze research sources with pie and bar charts
- **☁️ Content Analysis**: Generate word clouds from paper titles and keywords
- **⚡ Performance Optimization**: Smart data sampling and memory optimization
- **🛡️ Error Handling**: Comprehensive error handling with graceful degradation
- **🔧 Health Monitoring**: Built-in health checks and system monitoring

## 🚀 Live Demo

**[Try the app here!](https://your-app-url.streamlit.app/)**

## 📋 Requirements

- Python 3.8+
- Streamlit
- Pandas
- Plotly
- WordCloud
- Other dependencies listed in `requirements.txt`

## 🛠️ Installation

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/covid-research-analyzer.git
   cd covid-research-analyzer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run app.py
   ```

4. **Open your browser**
   Navigate to `http://localhost:8501`

### Using Docker

1. **Build the image**
   ```bash
   docker build -t covid-analyzer .
   ```

2. **Run the container**
   ```bash
   docker run -p 8501:8501 covid-analyzer
   ```

## 📊 Usage

### Getting Started

1. **Upload Data**: Use the sidebar to upload a CORD-19 metadata CSV file
2. **Or Use Sample Data**: Check "Use sample data for demo" to explore with sample data
3. **Explore Analysis**: Navigate through the tabs to explore different insights:
   - **Temporal Trends**: Publication counts over time
   - **Journal Analysis**: Top publishing journals
   - **Source Distribution**: Research source breakdown
   - **Content Analysis**: Keyword analysis and word clouds
   - **Data Overview**: Dataset statistics and sample viewer

### Data Format

The application expects CORD-19 metadata CSV files with the following columns:
- `paper_id`: Unique paper identifier
- `title`: Paper title
- `abstract`: Paper abstract (optional)
- `authors`: Author list (optional)
- `journal`: Journal name (optional)
- `source_x`: Data source (optional)
- `publish_time`: Publication date (optional)

### Features

#### 🎛️ Interactive Controls
- **Date Range Filter**: Filter publications by year
- **Journal Filter**: Select specific journals
- **Source Filter**: Filter by data source
- **Display Settings**: Customize number of items shown

#### 📈 Visualizations
- **Interactive Charts**: Hover, zoom, and pan functionality
- **Responsive Design**: Adapts to different screen sizes
- **Export Options**: Download charts and data

#### ⚡ Performance Features
- **Smart Sampling**: Automatic sampling for large datasets
- **Memory Optimization**: Efficient data type optimization
- **Caching**: Intelligent caching for faster performance

## 🏗️ Architecture

### Components

- **`app.py`**: Main Streamlit application
- **`data_loader.py`**: Data loading and validation
- **`data_processor.py`**: Data cleaning and preprocessing
- **`analyzer.py`**: Statistical analysis functions
- **`visualizer.py`**: Chart and visualization creation
- **`config.py`**: Configuration management
- **`health_check.py`**: Health monitoring system
- **`error_handler.py`**: Error handling and recovery
- **`performance_optimizer.py`**: Performance optimization
- **`logger_config.py`**: Logging and debugging

### Data Flow

```
Data Upload → Validation → Processing → Analysis → Visualization
     ↓            ↓           ↓          ↓           ↓
Error Handling ← Logging ← Caching ← Sampling ← Optimization
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
COVID_ANALYZER_ENVIRONMENT=production
COVID_ANALYZER_DEBUG=false
COVID_ANALYZER_LOG_LEVEL=INFO
COVID_ANALYZER_MAX_FILE_SIZE_MB=500
COVID_ANALYZER_ENABLE_SAMPLING=true
```

### Streamlit Configuration

Customize the app appearance in `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"

[server]
maxUploadSize = 500
```

## 🚀 Deployment

### Streamlit Cloud

1. **Push to GitHub**: Ensure your code is in a public GitHub repository
2. **Connect to Streamlit Cloud**: Visit [share.streamlit.io](https://share.streamlit.io/)
3. **Deploy**: Select your repository and deploy
4. **Configure**: Set environment variables in the app settings

### Docker Deployment

Use the provided Docker configuration:

```bash
docker-compose up -d
```

### Kubernetes

Deploy using the provided Kubernetes manifests:

```bash
kubectl apply -f deployment/kubernetes/
```

## 🧪 Testing

Run the test suite:

```bash
# Integration tests
python test_integration.py

# Deployment tests
python test_deployment_config.py

# Complete workflow test
python test_complete_workflow.py
```

## 📈 Performance

### Optimization Features

- **Data Sampling**: Automatic sampling for datasets > 10,000 rows
- **Memory Optimization**: Data type optimization reduces memory usage by ~20%
- **Caching**: Streamlit caching for expensive operations
- **Lazy Loading**: Components loaded on demand

### Benchmarks

- **Small datasets** (< 1,000 rows): < 2 seconds load time
- **Medium datasets** (1,000 - 10,000 rows): < 5 seconds load time
- **Large datasets** (> 10,000 rows): < 10 seconds with sampling

## 🛡️ Error Handling

The application includes comprehensive error handling:

- **Graceful Degradation**: Continues operation when non-critical components fail
- **User-Friendly Messages**: Clear error messages with recovery suggestions
- **Logging**: Detailed logging for debugging
- **Health Checks**: Built-in system health monitoring

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **CORD-19 Dataset**: COVID-19 Open Research Dataset by Semantic Scholar
- **Streamlit**: For the amazing web app framework
- **Plotly**: For interactive visualizations
- **WordCloud**: For text visualization capabilities

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/covid-research-analyzer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/YOUR_USERNAME/covid-research-analyzer/discussions)
- **Email**: your-email@example.com

## 🔗 Links

- **Live App**: [https://your-app-url.streamlit.app/](https://your-app-url.streamlit.app/)
- **CORD-19 Dataset**: [https://www.semanticscholar.org/cord19/download](https://www.semanticscholar.org/cord19/download)
- **Documentation**: [Deployment Guide](streamlit_deploy_guide.md)

---

**Built with ❤️ using Streamlit**