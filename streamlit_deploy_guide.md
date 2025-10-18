# Deploying COVID-19 Research Analyzer to Streamlit Cloud

## Prerequisites
1. GitHub account
2. Streamlit Cloud account (free at https://share.streamlit.io/)
3. Your application code ready

## Step-by-Step Deployment Process

### 1. Prepare Your Repository

#### A. Create/Update requirements.txt
Ensure your `requirements.txt` contains all dependencies:
```
streamlit>=1.28.0
pandas>=1.5.0
plotly>=5.15.0
wordcloud>=1.9.0
requests>=2.28.0
matplotlib>=3.6.0
pillow>=9.0.0
numpy>=1.24.0
psutil>=5.9.0
python-dotenv>=1.0.0
```

#### B. Create .streamlit/config.toml (optional)
```toml
[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"

[server]
headless = true
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false
```

#### C. Create .gitignore
```
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Environment variables
.env
*.env

# Streamlit
.streamlit/secrets.toml

# Data files (if large)
*.csv
*.json
data/

# Logs
*.log
logs/

# IDE
.vscode/
.idea/
*.swp
*.swo
```

### 2. Push to GitHub

#### A. Initialize Git Repository (if not already done)
```bash
git init
git add .
git commit -m "Initial commit: COVID-19 Research Analyzer"
```

#### B. Create GitHub Repository
1. Go to https://github.com
2. Click "New repository"
3. Name it "covid-research-analyzer"
4. Make it public (required for free Streamlit Cloud)
5. Don't initialize with README (since you already have files)

#### C. Push to GitHub
```bash
git remote add origin https://github.com/YOUR_USERNAME/covid-research-analyzer.git
git branch -M main
git push -u origin main
```

### 3. Deploy to Streamlit Cloud

#### A. Sign Up/Login to Streamlit Cloud
1. Go to https://share.streamlit.io/
2. Sign in with your GitHub account
3. Authorize Streamlit to access your repositories

#### B. Deploy Your App
1. Click "New app"
2. Select your repository: `YOUR_USERNAME/covid-research-analyzer`
3. Choose branch: `main`
4. Set main file path: `app.py`
5. Click "Deploy!"

#### C. Configure Environment Variables (if needed)
1. In your app dashboard, click "Settings"
2. Go to "Secrets"
3. Add any environment variables in TOML format:
```toml
COVID_ANALYZER_ENVIRONMENT = "production"
COVID_ANALYZER_DEBUG = "false"
COVID_ANALYZER_LOG_LEVEL = "INFO"
```

### 4. Monitor Deployment

#### A. Check Build Logs
- Streamlit Cloud will show build progress
- Watch for any errors in dependency installation
- Check that all imports work correctly

#### B. Test Your App
- Once deployed, test all functionality
- Upload sample data to verify data processing
- Check all visualizations work correctly

### 5. Update and Maintain

#### A. Making Updates
```bash
git add .
git commit -m "Update: description of changes"
git push origin main
```
- Streamlit Cloud automatically redeploys on push to main branch

#### B. Monitor Performance
- Check app metrics in Streamlit Cloud dashboard
- Monitor resource usage
- Review error logs if issues occur

## Common Issues and Solutions

### 1. Import Errors
- Ensure all dependencies are in requirements.txt
- Check for version conflicts
- Use specific versions if needed

### 2. File Size Limits
- Streamlit Cloud has file size limits
- Use .gitignore for large data files
- Consider using external data sources

### 3. Memory Issues
- Optimize data processing
- Use sampling for large datasets
- Implement caching strategically

### 4. Secrets Management
- Never commit API keys or passwords
- Use Streamlit secrets for sensitive data
- Set environment variables in app settings

## Best Practices

1. **Keep repository clean**: Use .gitignore effectively
2. **Optimize performance**: Implement caching and data sampling
3. **Handle errors gracefully**: Provide user-friendly error messages
4. **Document your app**: Include README with usage instructions
5. **Test thoroughly**: Verify all features work in cloud environment

## Your App URL
After deployment, your app will be available at:
`https://YOUR_USERNAME-covid-research-analyzer-app-main-hash.streamlit.app/`

## Support Resources
- Streamlit Documentation: https://docs.streamlit.io/
- Streamlit Community: https://discuss.streamlit.io/
- GitHub Issues: For code-specific problems