"""
Pharmaceutical Report HTML Template

Professional-grade HTML/CSS template for pharmaceutical intelligence reports.
Matches the visual style of the React frontend agent displays.

Features:
- Responsive design (A4/Letter PDF & screen)
- All agent data sections with appropriate visualizations
- Traffic light risk indicators
- Chart placeholders for Recharts data
- Print-optimized CSS
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json


class PharmReportTemplate:
    """
    HTML Template Generator for Pharmaceutical Intelligence Reports.
    
    Produces professional pharmaceutical reports with:
    - Cover page with drug/indication branding
    - Executive summary with key metrics
    - All 6 agent data sections
    - Strategic recommendations
    - Print-ready PDF styling
    """
    
    # Color scheme matching frontend
    COLORS = {
        "primary": "#1e40af",
        "primary_light": "#3b82f6",
        "secondary": "#7c3aed",
        "secondary_light": "#a78bfa",
        "iqvia": "#3b82f6",         # blue
        "clinical": "#10b981",      # emerald
        "patent": "#f59e0b",        # amber
        "exim": "#14b8a6",          # teal
        "internal": "#ec4899",      # pink
        "web": "#06b6d4",           # cyan
        "report": "#8b5cf6",        # violet
        "success": "#10b981",
        "warning": "#f59e0b",
        "danger": "#ef4444",
        "neutral": "#6b7280",
        "background": "#0f172a",
        "card": "#1e293b",
        "border": "#334155",
        "text": "#f8fafc",
        "text_muted": "#94a3b8",
    }
    
    # Chart colors matching frontend palette
    CHART_COLORS = [
        "#003f5c", "#2f4b7c", "#665191", "#a05195",
        "#d45087", "#f95d6a", "#ff7c43", "#ffa600"
    ]
    
    def __init__(self):
        self.css = self._generate_css()
        
    def _generate_css(self) -> str:
        """Generate comprehensive CSS for the report - Production-grade aesthetic"""
        return """
        /* ============================================
           PHARMASSIST INTELLIGENCE REPORT
           Production-Grade Template | 2026
           Aesthetic: Editorial Pharmaceutical
           ============================================ */
        
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700;800&family=DM+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
        
        :root {
            /* Core Brand - Deep Ocean meets Pharmaceutical Precision */
            --primary: #0c4a6e;
            --primary-light: #0ea5e9;
            --primary-glow: #38bdf8;
            --secondary: #4f46e5;
            --secondary-light: #818cf8;
            --accent: #06b6d4;
            --accent-warm: #f59e0b;
            
            /* Agent Signature Colors */
            --iqvia: #0891b2;
            --clinical: #059669;
            --patent: #d97706;
            --exim: #0d9488;
            --internal: #be185d;
            --web: #0284c7;
            --report: #7c3aed;
            
            /* Semantic Indicators */
            --success: #10b981;
            --success-soft: #d1fae5;
            --warning: #f59e0b;
            --warning-soft: #fef3c7;
            --danger: #ef4444;
            --danger-soft: #fee2e2;
            --neutral: #64748b;
            
            /* Surface System - Elegant Dark Theme */
            --background: #0a0f1a;
            --background-elevated: #0f172a;
            --surface: #1e293b;
            --surface-light: #334155;
            --surface-hover: #3f4f63;
            --border: #475569;
            --border-subtle: #334155;
            
            /* Typography Colors */
            --text: #f1f5f9;
            --text-secondary: #cbd5e1;
            --text-muted: #94a3b8;
            --text-faint: #64748b;
            
            /* Shadows & Glows */
            --shadow-sm: 0 2px 8px rgba(0,0,0,0.3);
            --shadow-md: 0 8px 24px rgba(0,0,0,0.4);
            --shadow-lg: 0 16px 48px rgba(0,0,0,0.5);
            --shadow-glow: 0 0 40px rgba(14, 165, 233, 0.15);
            --shadow-accent: 0 4px 20px rgba(6, 182, 212, 0.3);
        }
        
        /* ============================================
           BASE STYLES
           ============================================ */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        html, body {
            font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 15px;
            line-height: 1.7;
            color: var(--text);
            background: var(--background);
            font-feature-settings: 'kern' 1, 'liga' 1;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }
        
        /* Print Optimization */
        @media print {
            * {
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
            }
            
            html, body {
                background: #ffffff;
                color: #0f172a;
                font-size: 12px;
            }
            
            :root {
                --background: #ffffff;
                --background-elevated: #f8fafc;
                --surface: #f1f5f9;
                --surface-light: #e2e8f0;
                --border: #cbd5e1;
                --text: #0f172a;
                --text-secondary: #334155;
                --text-muted: #64748b;
            }
            
            .page-break {
                page-break-before: always;
                break-before: page;
            }
            
            .no-print { display: none !important; }
            .section { break-inside: avoid; }
        }
        
        /* ============================================
           LAYOUT CONTAINER
           ============================================ */
        .report-container {
            max-width: 210mm;
            margin: 0 auto;
            background: var(--background);
            min-height: 100vh;
            position: relative;
        }
        
        @media screen {
            .report-container {
                max-width: 920px;
                margin: 32px auto;
                border-radius: 24px;
                box-shadow: var(--shadow-lg), var(--shadow-glow);
                overflow: hidden;
                border: 1px solid var(--border-subtle);
            }
        }
        
        /* ============================================
           COVER PAGE - Editorial Luxury
           ============================================ */
        .cover-page {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 64px 56px;
            background: 
                radial-gradient(ellipse at 20% 0%, rgba(14, 165, 233, 0.12) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 100%, rgba(79, 70, 229, 0.08) 0%, transparent 50%),
                linear-gradient(180deg, var(--background) 0%, var(--background-elevated) 100%);
            position: relative;
            overflow: hidden;
        }
        
        .cover-page::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 5px;
            background: linear-gradient(90deg, 
                var(--primary-light) 0%, 
                var(--accent) 25%, 
                var(--secondary-light) 50%, 
                var(--accent) 75%, 
                var(--primary-light) 100%
            );
        }
        
        .cover-page::after {
            content: '';
            position: absolute;
            bottom: -200px;
            right: -200px;
            width: 600px;
            height: 600px;
            background: radial-gradient(circle, rgba(6, 182, 212, 0.06) 0%, transparent 70%);
            border-radius: 50%;
            pointer-events: none;
        }
        
        .cover-header {
            position: relative;
            z-index: 2;
        }
        
        .cover-logo {
            font-family: 'DM Sans', sans-serif;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 5px;
            color: var(--accent);
            margin-bottom: 80px;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .cover-logo::before {
            content: '◆';
            font-size: 8px;
        }
        
        .cover-title {
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 52px;
            font-weight: 700;
            color: var(--text);
            line-height: 1.1;
            letter-spacing: -1px;
            margin-bottom: 16px;
        }
        
        .cover-subtitle {
            font-family: 'DM Sans', sans-serif;
            font-size: 18px;
            font-weight: 400;
            color: var(--text-muted);
            letter-spacing: 0.5px;
        }
        
        .cover-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            position: relative;
            z-index: 2;
            padding: 40px 0;
        }
        
        .cover-drug-box {
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            padding: 32px 72px;
            border-radius: 20px;
            font-family: 'Playfair Display', serif;
            font-size: 36px;
            font-weight: 700;
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-bottom: 28px;
            box-shadow: var(--shadow-lg), var(--shadow-accent);
            position: relative;
            overflow: hidden;
        }
        
        .cover-drug-box::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, transparent 50%);
            pointer-events: none;
        }
        
        .cover-indication {
            font-family: 'DM Sans', sans-serif;
            font-size: 18px;
            font-weight: 500;
            color: var(--success);
            letter-spacing: 1px;
        }
        
        .cover-footer {
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            padding-top: 32px;
            border-top: 1px solid var(--border-subtle);
            position: relative;
            z-index: 2;
        }
        
        .cover-info-box {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 28px 40px;
        }
        
        .cover-info-item {
            font-size: 13px;
            color: var(--text-muted);
            margin: 6px 0;
            font-weight: 400;
        }
        
        .cover-info-item strong {
            color: var(--text);
            font-weight: 600;
        }
        
        /* ============================================
           EXECUTIVE SUMMARY - Hero Section
           ============================================ */
        .executive-summary {
            padding: 56px;
            background: linear-gradient(180deg, var(--background-elevated) 0%, var(--background) 100%);
        }
        
        .opportunity-score-card {
            background: 
                radial-gradient(ellipse at 50% 0%, rgba(14, 165, 233, 0.08) 0%, transparent 60%),
                var(--surface);
            border: 1px solid var(--border);
            border-radius: 24px;
            padding: 48px;
            text-align: center;
            margin-bottom: 40px;
            position: relative;
            overflow: hidden;
        }
        
        .opportunity-score-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--success), var(--primary-light), var(--accent));
        }
        
        .opportunity-score-label {
            font-family: 'DM Sans', sans-serif;
            font-size: 11px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 3px;
            margin-bottom: 20px;
        }
        
        .opportunity-score-value {
            font-family: 'Playfair Display', serif;
            font-size: 96px;
            font-weight: 800;
            background: linear-gradient(135deg, var(--success) 0%, var(--primary-light) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1;
            margin-bottom: 8px;
        }
        
        .opportunity-score-value.medium {
            background: linear-gradient(135deg, var(--warning) 0%, var(--accent-warm) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .opportunity-score-value.low {
            background: linear-gradient(135deg, var(--danger) 0%, var(--warning) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .opportunity-score-max {
            font-family: 'DM Sans', sans-serif;
            font-size: 24px;
            color: var(--text-faint);
            font-weight: 400;
        }
        
        .key-takeaways {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 32px;
            margin-bottom: 32px;
        }
        
        .key-takeaways h3 {
            font-family: 'DM Sans', sans-serif;
            font-size: 14px;
            font-weight: 600;
            color: var(--text);
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .key-takeaways ul {
            list-style: none;
            padding: 0;
        }
        
        .key-takeaways li {
            padding: 16px 20px;
            margin: 10px 0;
            background: linear-gradient(90deg, rgba(14, 165, 233, 0.08) 0%, transparent 100%);
            border-left: 3px solid var(--primary-light);
            border-radius: 0 12px 12px 0;
            font-size: 14px;
            color: var(--text-secondary);
            line-height: 1.6;
        }
        
        .recommendation-card {
            background: 
                linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(6, 182, 212, 0.05) 100%),
                var(--surface);
            border: 2px solid var(--success);
            border-radius: 20px;
            padding: 32px;
            position: relative;
        }
        
        .recommendation-card.moderate {
            background: 
                linear-gradient(135deg, rgba(245, 158, 11, 0.08) 0%, rgba(6, 182, 212, 0.05) 100%),
                var(--surface);
            border-color: var(--warning);
        }
        
        .recommendation-card.limited {
            background: 
                linear-gradient(135deg, rgba(239, 68, 68, 0.08) 0%, rgba(245, 158, 11, 0.05) 100%),
                var(--surface);
            border-color: var(--danger);
        }
        
        .recommendation-label {
            font-family: 'DM Sans', sans-serif;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: var(--success);
            margin-bottom: 12px;
        }
        
        .recommendation-text {
            font-family: 'DM Sans', sans-serif;
            font-size: 17px;
            font-weight: 500;
            color: var(--text);
            line-height: 1.6;
        }
        
        /* ============================================
           SECTION HEADERS - Editorial Style
           ============================================ */
        .section {
            padding: 48px 56px;
            border-bottom: 1px solid var(--border-subtle);
        }
        
        .section:last-of-type {
            border-bottom: none;
        }
        
        .section-header {
            display: flex;
            align-items: flex-start;
            gap: 20px;
            margin-bottom: 32px;
            padding-bottom: 24px;
            border-bottom: 1px solid var(--border-subtle);
        }
        
        .section-icon {
            width: 56px;
            height: 56px;
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 26px;
            flex-shrink: 0;
            box-shadow: var(--shadow-sm);
        }
        
        .section-icon.iqvia { 
            background: linear-gradient(135deg, var(--iqvia) 0%, #0e7490 100%);
            color: white;
        }
        .section-icon.clinical { 
            background: linear-gradient(135deg, var(--clinical) 0%, #047857 100%);
            color: white;
        }
        .section-icon.patent { 
            background: linear-gradient(135deg, var(--patent) 0%, #b45309 100%);
            color: white;
        }
        .section-icon.exim { 
            background: linear-gradient(135deg, var(--exim) 0%, #0f766e 100%);
            color: white;
        }
        .section-icon.internal { 
            background: linear-gradient(135deg, var(--internal) 0%, #9d174d 100%);
            color: white;
        }
        .section-icon.web { 
            background: linear-gradient(135deg, var(--web) 0%, #0369a1 100%);
            color: white;
        }
        
        .section-title {
            font-family: 'Playfair Display', serif;
            font-size: 28px;
            font-weight: 700;
            color: var(--text);
            margin-bottom: 4px;
        }
        
        .section-subtitle {
            font-family: 'DM Sans', sans-serif;
            font-size: 14px;
            color: var(--text-muted);
            font-weight: 400;
        }
        
        /* ============================================
           SUMMARY BANNERS - Signal Cards
           ============================================ */
        .summary-banner {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px 28px;
            margin-bottom: 28px;
            position: relative;
            overflow: hidden;
        }
        
        .summary-banner::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
        }
        
        .summary-banner.iqvia::before { background: var(--iqvia); }
        .summary-banner.clinical::before { background: var(--clinical); }
        .summary-banner.patent::before { background: var(--patent); }
        .summary-banner.exim::before { background: var(--exim); }
        .summary-banner.internal::before { background: var(--internal); }
        .summary-banner.web::before { background: var(--web); }
        
        .summary-question {
            font-family: 'DM Sans', sans-serif;
            font-size: 12px;
            font-weight: 500;
            color: var(--text-muted);
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .summary-answer {
            font-family: 'Playfair Display', serif;
            font-size: 22px;
            font-weight: 600;
            margin-bottom: 16px;
        }
        
        .summary-answer.positive { color: var(--success); }
        .summary-answer.neutral { color: var(--warning); }
        .summary-answer.negative { color: var(--danger); }
        
        .summary-explainers {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        
        .summary-explainer {
            font-family: 'DM Sans', sans-serif;
            font-size: 11px;
            font-weight: 500;
            padding: 6px 14px;
            background: var(--surface-light);
            border-radius: 20px;
            color: var(--text-muted);
            border: 1px solid var(--border-subtle);
        }
        
        /* ============================================
           METRIC CARDS - Data Visualization
           ============================================ */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }
        
        .metric-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            transition: all 0.2s ease;
        }
        
        .metric-card:hover {
            border-color: var(--primary-light);
            box-shadow: var(--shadow-sm);
        }
        
        .metric-label {
            font-family: 'DM Sans', sans-serif;
            font-size: 11px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 12px;
        }
        
        .metric-value {
            font-family: 'Playfair Display', serif;
            font-size: 32px;
            font-weight: 700;
            color: var(--primary-light);
            line-height: 1;
        }
        
        .metric-unit {
            font-family: 'DM Sans', sans-serif;
            font-size: 14px;
            color: var(--text-muted);
            font-weight: 400;
            margin-left: 2px;
        }
        
        .metric-trend {
            font-family: 'DM Sans', sans-serif;
            font-size: 12px;
            margin-top: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            font-weight: 500;
        }
        
        .metric-trend.up { color: var(--success); }
        .metric-trend.down { color: var(--danger); }
        .metric-trend.neutral { color: var(--text-muted); }
        
        /* ============================================
           DATA TABLES - Clean & Professional
           ============================================ */
        .data-table-container {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            overflow: hidden;
            margin-bottom: 28px;
        }
        
        .data-table-title {
            font-family: 'DM Sans', sans-serif;
            font-size: 13px;
            font-weight: 600;
            padding: 18px 24px;
            background: var(--surface-light);
            border-bottom: 1px solid var(--border);
            color: var(--text);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .data-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .data-table th {
            text-align: left;
            padding: 14px 24px;
            font-family: 'DM Sans', sans-serif;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-muted);
            background: var(--surface-light);
            border-bottom: 1px solid var(--border);
        }
        
        .data-table td {
            padding: 16px 24px;
            font-family: 'DM Sans', sans-serif;
            font-size: 13px;
            color: var(--text-secondary);
            border-bottom: 1px solid var(--border-subtle);
        }
        
        .data-table tr:last-child td {
            border-bottom: none;
        }
        
        .data-table tr:hover td {
            background: var(--surface-hover);
        }
        
        /* ============================================
           BADGES & STATUS INDICATORS
           ============================================ */
        .badge {
            display: inline-flex;
            align-items: center;
            padding: 6px 14px;
            border-radius: 20px;
            font-family: 'DM Sans', sans-serif;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .badge.high { 
            background: var(--danger-soft); 
            color: var(--danger);
            border: 1px solid rgba(239, 68, 68, 0.3);
        }
        .badge.medium { 
            background: var(--warning-soft); 
            color: #b45309;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }
        .badge.low { 
            background: var(--success-soft); 
            color: #047857;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        .badge.clear { background: var(--success-soft); color: #047857; }
        .badge.at-risk { background: var(--warning-soft); color: #b45309; }
        .badge.blocked { background: var(--danger-soft); color: var(--danger); }
        
        .status-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-dot.green { background: var(--success); box-shadow: 0 0 8px rgba(16, 185, 129, 0.5); }
        .status-dot.amber, .status-dot.yellow { background: var(--warning); box-shadow: 0 0 8px rgba(245, 158, 11, 0.5); }
        .status-dot.red { background: var(--danger); box-shadow: 0 0 8px rgba(239, 68, 68, 0.5); }
        .status-dot.blue { background: var(--primary-light); box-shadow: 0 0 8px rgba(14, 165, 233, 0.5); }
        
        /* ============================================
           CHART CONTAINERS
           ============================================ */
        .chart-container {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 28px;
            margin-bottom: 28px;
        }
        
        .chart-title {
            font-family: 'DM Sans', sans-serif;
            font-size: 13px;
            font-weight: 600;
            color: var(--text);
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .chart-placeholder {
            background: var(--surface-light);
            border: 2px dashed var(--border);
            border-radius: 12px;
            height: 280px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-muted);
            font-size: 13px;
        }
        
        .chart-svg {
            width: 100%;
            height: 280px;
        }
        
        .chart-svg .axis-line {
            stroke: var(--border);
            stroke-width: 1;
        }
        
        .chart-svg .grid-line {
            stroke: var(--border-subtle);
            stroke-width: 0.5;
            stroke-dasharray: 4 4;
            opacity: 0.5;
        }
        
        .chart-svg .bar {
            rx: 6;
        }
        
        .chart-svg .label {
            fill: var(--text-muted);
            font-family: 'DM Sans', sans-serif;
            font-size: 11px;
        }
        
        .chart-svg .value-label {
            fill: var(--text);
            font-family: 'Playfair Display', serif;
            font-size: 13px;
            font-weight: 600;
        }
        
        /* Donut Chart Styling */
        .donut-chart-container {
            display: flex;
            align-items: center;
            gap: 48px;
            justify-content: center;
            padding: 20px 0;
        }
        
        .donut-legend {
            display: flex;
            flex-direction: column;
            gap: 14px;
        }
        
        .donut-legend-item {
            display: flex;
            align-items: center;
            gap: 14px;
        }
        
        .donut-legend-color {
            width: 14px;
            height: 14px;
            border-radius: 4px;
            flex-shrink: 0;
        }
        
        .donut-legend-label {
            font-family: 'DM Sans', sans-serif;
            font-size: 13px;
            color: var(--text-secondary);
            flex: 1;
            min-width: 120px;
        }
        
        .donut-legend-value {
            font-family: 'Playfair Display', serif;
            font-size: 14px;
            font-weight: 600;
            color: var(--primary-light);
        }
        
        /* ============================================
           STRATEGIC RECOMMENDATIONS
           ============================================ */
        .priority-matrix {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            margin-bottom: 28px;
        }
        
        .priority-item {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px;
            position: relative;
            overflow: hidden;
        }
        
        .priority-item::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
        }
        
        .priority-item.high::before { background: var(--danger); }
        .priority-item.medium::before { background: var(--warning); }
        .priority-item.low::before { background: var(--success); }
        
        .priority-label {
            font-family: 'DM Sans', sans-serif;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
        
        .priority-item.high .priority-label { color: var(--danger); }
        .priority-item.medium .priority-label { color: var(--warning); }
        .priority-item.low .priority-label { color: var(--success); }
        
        .priority-title {
            font-family: 'DM Sans', sans-serif;
            font-size: 15px;
            font-weight: 600;
            color: var(--text);
            margin-bottom: 8px;
        }
        
        .priority-description {
            font-family: 'DM Sans', sans-serif;
            font-size: 13px;
            color: var(--text-muted);
            line-height: 1.5;
        }
        
        /* ============================================
           APPENDIX & RAW DATA
           ============================================ */
        .appendix-section {
            margin-bottom: 36px;
        }
        
        .appendix-title {
            font-family: 'Playfair Display', serif;
            font-size: 20px;
            font-weight: 600;
            color: var(--text);
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border);
        }
        
        .raw-data-block {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            font-family: 'JetBrains Mono', Monaco, Consolas, monospace;
            font-size: 11px;
            color: var(--text-muted);
            overflow-x: auto;
            white-space: pre-wrap;
            line-height: 1.6;
        }
        
        /* ============================================
           FOOTER - Refined
           ============================================ */
        .report-footer {
            padding: 40px 56px;
            background: var(--surface);
            border-top: 1px solid var(--border);
            text-align: center;
        }
        
        .report-footer p {
            font-family: 'DM Sans', sans-serif;
            font-size: 12px;
            color: var(--text-muted);
            margin: 6px 0;
        }
        
        .report-footer strong {
            color: var(--text-secondary);
        }
        
        /* ============================================
           UTILITIES
           ============================================ */
        .text-center { text-align: center; }
        .text-right { text-align: right; }
        .mt-4 { margin-top: 16px; }
        .mb-4 { margin-bottom: 16px; }
        .flex { display: flex; }
        .flex-wrap { flex-wrap: wrap; }
        .gap-4 { gap: 16px; }
        .items-center { align-items: center; }
        .justify-between { justify-content: space-between; }
        
        /* Page Break */
        .page-break {
            page-break-before: always;
            break-before: page;
            height: 0;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .report-container {
                margin: 0;
                border-radius: 0;
            }
            
            .cover-page, .section, .executive-summary {
                padding: 32px 24px;
            }
            
            .cover-title {
                font-size: 36px;
            }
            
            .cover-drug-box {
                padding: 24px 40px;
                font-size: 24px;
            }
            
            .metrics-grid {
                grid-template-columns: 1fr 1fr;
            }
            
            .priority-matrix {
                grid-template-columns: 1fr;
            }
            
            .donut-chart-container {
                flex-direction: column;
                gap: 24px;
            }
        }
        """
    
    def _render_cover_page(self, drug_name: str, indication: str, report_date: str) -> str:
        """Render the cover page HTML - Editorial luxury design"""
        return f"""
        <div class="cover-page">
            <div class="cover-header">
                <div class="cover-logo">PharmAssist Intelligence</div>
                <h1 class="cover-title">Pharmaceutical<br/>Intelligence Report</h1>
                <p class="cover-subtitle">Comprehensive Drug Repurposing & Market Analysis</p>
            </div>
            
            <div class="cover-content">
                <div class="cover-drug-box">{drug_name.upper()}</div>
                <p class="cover-indication">▸ {indication.upper() if indication and indication.lower() != 'general' else 'COMPREHENSIVE ANALYSIS'}</p>
            </div>
            
            <div class="cover-footer">
                <div class="cover-info-box">
                    <p class="cover-info-item"><strong>Report Date:</strong> {report_date}</p>
                    <p class="cover-info-item"><strong>Generated by:</strong> PharmAssist Multi-Agent System</p>
                    <p class="cover-info-item" style="margin-top: 12px; font-size: 11px; opacity: 0.7;">Confidential — For Internal Use Only</p>
                </div>
            </div>
        </div>
        
        <div class="page-break"></div>
        """
    
    def _render_executive_summary(self, data: Dict) -> str:
        """Render executive summary section - Hero styling"""
        score = data.get("opportunity_score", 0)
        score_class = "high" if score >= 75 else "medium" if score >= 50 else "low"
        
        takeaways = data.get("key_takeaways", [])
        recommendation = data.get("recommendation", "")
        rec_class = "strong" if score >= 75 else "moderate" if score >= 50 else "limited"
        
        takeaways_html = "\n".join([f'<li>{t}</li>' for t in takeaways]) if takeaways else '<li>Analysis in progress...</li>'
        
        return f"""
        <div class="executive-summary">
            <div class="section-header">
                <div class="section-icon" style="background: linear-gradient(135deg, #7c3aed 0%, #6366f1 100%); color: white;">📊</div>
                <div>
                    <h2 class="section-title">Executive Summary</h2>
                    <p class="section-subtitle">Key findings and strategic recommendation</p>
                </div>
            </div>
            
            <div class="opportunity-score-card">
                <p class="opportunity-score-label">Overall Opportunity Score</p>
                <div class="opportunity-score-value {score_class}">{score:.0f}<span class="opportunity-score-max">/100</span></div>
            </div>
            
            <div class="key-takeaways">
                <h3>🎯 Key Takeaways</h3>
                <ul>
                    {takeaways_html}
                </ul>
            </div>
            
            <div class="recommendation-card {rec_class}">
                <p class="recommendation-label">▸ Strategic Recommendation</p>
                <p class="recommendation-text">{recommendation or 'Analysis in progress...'}</p>
            </div>
        </div>
        """
    
    def _render_iqvia_section(self, data: Dict) -> str:
        """Render IQVIA Market Intelligence section - handles actual agent data"""
        iqvia = data.get("iqvia", {})
        if not iqvia:
            return ""
        
        actual_data = iqvia.get("data", iqvia)
        
        # Summary banner
        summary = actual_data.get("summary", {})
        summary_html = ""
        if summary:
            answer = summary.get("answer", "")
            answer_class = "positive" if "Yes" in answer or "High" in answer else "neutral" if "Stable" in answer else "negative"
            explainers = summary.get("explainers", [])
            explainers_html = " ".join([f'<span class="summary-explainer">{e}</span>' for e in explainers])
            
            summary_html = f"""
            <div class="summary-banner iqvia">
                <p class="summary-question">{summary.get('researcherQuestion', 'Is this worth exploring commercially?')}</p>
                <p class="summary-answer {answer_class}">{answer}</p>
                <div class="summary-explainers">{explainers_html}</div>
            </div>
            """
        
        # Metrics
        metrics_html = ""
        market_size = actual_data.get("marketSizeUSD")
        cagr = actual_data.get("cagrPercent")
        total_growth = actual_data.get("totalGrowthPercent")
        start_market = actual_data.get("startMarketSize")
        market_leader = actual_data.get("marketLeader", {})
        
        metrics = []
        if market_size:
            metrics.append(f'<div class="metric-card"><p class="metric-label">Market Size (2027)</p><p class="metric-value">${market_size:.1f}<span class="metric-unit">B</span></p></div>')
        if start_market:
            metrics.append(f'<div class="metric-card"><p class="metric-label">Current Market</p><p class="metric-value">${start_market:.1f}<span class="metric-unit">B</span></p></div>')
        if cagr:
            trend = "up" if cagr > 5 else "neutral"
            metrics.append(f'<div class="metric-card"><p class="metric-label">CAGR</p><p class="metric-value">{cagr:.1f}<span class="metric-unit">%</span></p><p class="metric-trend {trend}">{"↑" if trend == "up" else "→"} Growth</p></div>')
        if total_growth:
            metrics.append(f'<div class="metric-card"><p class="metric-label">Total Growth</p><p class="metric-value">{total_growth:.1f}<span class="metric-unit">%</span></p></div>')
        if market_leader:
            leader_name = market_leader.get("therapy", "N/A")
            leader_share = market_leader.get("share", market_leader.get("shareValue", ""))
            metrics.append(f'<div class="metric-card"><p class="metric-label">Market Leader</p><p class="metric-value" style="font-size: 18px;">{leader_name}</p><p class="metric-trend neutral">{leader_share}</p></div>')
        
        if metrics:
            metrics_html = f'<div class="metrics-grid">{"".join(metrics)}</div>'
        
        # Market forecast chart from data
        market_forecast = actual_data.get("market_forecast", {})
        forecast_html = ""
        if market_forecast and market_forecast.get("data"):
            forecast_data = market_forecast["data"]
            forecast_html = self._render_bar_chart(
                title=market_forecast.get("title", "Market Growth Trajectory"),
                data=forecast_data,
                x_field="year",
                y_field="value",
                color=self.COLORS["iqvia"]
            )
        
        # Competitive share chart from topTherapies (actual agent data)
        top_therapies = actual_data.get("topTherapies", [])
        competitive_html = ""
        if top_therapies:
            # Convert topTherapies to competitive share format
            competitive_data = [{"company": t.get("therapy", "Unknown"), "share": t.get("share", "0%")} for t in top_therapies]
            competitive_html = self._render_pie_chart(
                title="Competitive Market Share",
                data=competitive_data,
                label_field="company",
                value_field="share"
            )
        else:
            # Fallback to old format
            competitive_share = actual_data.get("competitive_share", {})
            if competitive_share and competitive_share.get("data"):
                competitive_html = self._render_pie_chart(
                    title=competitive_share.get("title", "Competitive Landscape"),
                    data=competitive_share["data"],
                    label_field="company",
                    value_field="share"
                )
        
        # Top articles section
        top_articles = actual_data.get("topArticles", [])
        articles_html = ""
        if top_articles:
            items = ""
            for article in top_articles[:3]:  # Top 3 articles
                title = article.get("title", "")
                source = article.get("source", "")
                snippet = article.get("snippet", "")
                items += f'''
                <div style="padding: 12px; background: rgba(93, 99, 255, 0.05); border: 1px solid rgba(93, 99, 255, 0.2); border-radius: 8px; margin-bottom: 8px;">
                    <p style="font-size: 13px; font-weight: 500; color: var(--text); margin-bottom: 4px;">{title}</p>
                    <p style="font-size: 11px; color: var(--text-muted);">
                        <span style="color: var(--iqvia);">{source}</span>
                    </p>
                    {f'<p style="font-size: 12px; color: var(--text-muted); margin-top: 6px;">{snippet[:100]}...</p>' if snippet else ''}
                </div>
                '''
            articles_html = f'''
            <div class="chart-container" style="margin-top: 16px;">
                <p class="chart-title">Market Research & Reports</p>
                {items}
            </div>
            '''
        
        return f"""
        <div class="section">
            <div class="section-header">
                <div class="section-icon iqvia">📈</div>
                <div>
                    <h2 class="section-title">Market Intelligence</h2>
                    <p class="section-subtitle">IQVIA Insights — Market size, growth & competitive analysis</p>
                </div>
            </div>
            
            {summary_html}
            {metrics_html}
            {forecast_html}
            {competitive_html}
            {articles_html}
        </div>
        """
    
    def _render_clinical_section(self, data: Dict) -> str:
        """Render Clinical Trials section - handles actual agent data structure"""
        clinical = data.get("clinical", {})
        if not clinical:
            return ""
        
        actual_data = clinical.get("data", clinical)
        
        # Build overview from summary if available
        summary = actual_data.get("summary", {})
        overview_html = ""
        if summary:
            answer = summary.get("answer", "Unknown")
            explainers = summary.get("explainers", [])
            explainers_html = " ".join([f'<span class="summary-explainer">{e}</span>' for e in explainers])
            
            overview_html = f"""
            <div class="summary-banner clinical">
                <p class="summary-question">{summary.get('researcherQuestion', 'Is there clinical evidence?')}</p>
                <p class="summary-answer neutral">{answer}</p>
                <div class="summary-explainers">{explainers_html}</div>
            </div>
            """
        
        # Build phase distribution from analysis data
        analysis = actual_data.get("analysis", {})
        phase_html = ""
        if analysis and analysis.get("phase_distribution"):
            phase_dist = analysis["phase_distribution"]
            total_trials = analysis.get("total_trials", 0)
            
            metrics = []
            for phase, count in phase_dist.items():
                color = "green" if "3" in phase or "4" in phase else "blue"
                metrics.append(f'''
                <div class="metric-card">
                    <p class="metric-label">{phase}</p>
                    <p class="metric-value">~{count}<span class="metric-unit">trials</span></p>
                    <p class="metric-trend neutral"><span class="status-dot {color}"></span>Active</p>
                </div>
                ''')
            phase_html = f'''
            <div class="chart-container">
                <p class="chart-title">Clinical Trial Phase Distribution</p>
                <div class="metrics-grid">{"".join(metrics)}</div>
                <p style="color: var(--text-muted); font-size: 13px; margin-top: 16px;">Total trials analyzed: {total_trials}</p>
            </div>
            '''
        
        # Build sponsor info from trials data
        trials_data = actual_data.get("trials", {})
        sponsor_html = ""
        if isinstance(trials_data, dict) and trials_data.get("trials"):
            trials_list = trials_data["trials"]
            
            # Extract and count sponsors
            sponsors = {}
            for trial in trials_list[:20]:  # First 20 trials
                sponsor = trial.get("sponsor", trial.get("lead_sponsor", "Unknown"))
                sponsors[sponsor] = sponsors.get(sponsor, 0) + 1
            
            if sponsors:
                rows = ""
                for sponsor, count in list(sorted(sponsors.items(), key=lambda x: -x[1]))[:5]:
                    rows += f'''
                    <tr>
                        <td>{sponsor}</td>
                        <td style="color: var(--clinical);">~{count}</td>
                        <td>Clinical Research</td>
                    </tr>
                    '''
                sponsor_html = f'''
                <div class="data-table-container">
                    <p class="data-table-title">Top Clinical Trial Sponsors</p>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Sponsor</th>
                                <th>Trials</th>
                                <th>Focus Area</th>
                            </tr>
                        </thead>
                        <tbody>{rows}</tbody>
                    </table>
                </div>
                '''
        
        return f"""
        <div class="section">
            <div class="section-header">
                <div class="section-icon clinical">🧬</div>
                <div>
                    <h2 class="section-title">Clinical Landscape</h2>
                    <p class="section-subtitle">Clinical Trials — Pipeline analysis & trial intelligence</p>
                </div>
            </div>
            
            {overview_html}
            {phase_html}
            {sponsor_html}
        </div>
        """
    
    def _render_patent_section(self, data: Dict) -> str:
        """Render Patent Landscape section - handles actual agent data structure"""
        patent = data.get("patent", {})
        if not patent:
            return ""
        
        actual_data = patent.get("data", patent)
        
        # Build summary banner from actual patent data
        fto_status = actual_data.get("ftoStatus", "UNKNOWN")
        patents_found = actual_data.get("patentsFound", 0)
        risk_level = actual_data.get("normalizedRiskInternal", 0)
        
        answer_class = "positive" if fto_status == "CLEAR" else "neutral" if fto_status == "AT_RISK" else "negative"
        
        # Build explainers
        explainers = []
        explainers.append(f"Patents found: {patents_found}")
        explainers.append(f"Risk level: {risk_level}")
        blocking_summary = actual_data.get("blockingPatentsSummary", {})
        if blocking_summary.get("count", 0) > 0:
            explainers.append(f"Blocking patents: {blocking_summary['count']}")
        
        explainers_html = " ".join([f'<span class="summary-explainer">{e}</span>' for e in explainers])
        
        summary_html = f"""
        <div class="summary-banner patent">
            <p class="summary-question">Is there Freedom to Operate (FTO)?</p>
            <p class="summary-answer {answer_class}">{fto_status}</p>
            <div class="summary-explainers">{explainers_html}</div>
        </div>
        """
        
        # Build overview metrics
        metrics = []
        metrics.append(f'<div class="metric-card"><p class="metric-label">FTO Status</p><p class="metric-value" style="font-size: 16px;">{fto_status}</p></div>')
        metrics.append(f'<div class="metric-card"><p class="metric-label">Patents Found</p><p class="metric-value" style="font-size: 16px;">{patents_found}</p></div>')
        metrics.append(f'<div class="metric-card"><p class="metric-label">Risk Score</p><p class="metric-value" style="font-size: 16px;">{risk_level}/100</p></div>')
        if blocking_summary:
            metrics.append(f'<div class="metric-card"><p class="metric-label">Blocking Patents</p><p class="metric-value" style="font-size: 16px;">{blocking_summary.get("count", 0)}</p></div>')
        
        overview_html = f'<div class="metrics-grid">{"".join(metrics)}</div>'
        
        # Recommended actions table
        actions = actual_data.get("recommendedActions", [])
        actions_html = ""
        if actions:
            rows = ""
            for action in actions[:5]:
                feasibility = action.get("feasibility", "MEDIUM")
                feasibility_class = "positive" if feasibility == "HIGH" else "neutral" if feasibility == "MEDIUM" else "negative"
                rows += f'''
                <tr>
                    <td>{action.get("action", "")}</td>
                    <td>{action.get("reason", "")}</td>
                    <td class="{feasibility_class}">{feasibility}</td>
                </tr>
                '''
            actions_html = f'''
            <div class="data-table-container">
                <p class="data-table-title">Recommended Patent Strategy Actions</p>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Action</th>
                            <th>Reason</th>
                            <th>Feasibility</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
            '''
        
        # Summary layers from patent analysis
        summary_layers = actual_data.get("summaryLayers", {})
        layers_html = ""
        if summary_layers:
            executive = summary_layers.get("executive", "")
            business = summary_layers.get("business", "")
            if executive or business:
                layers_html = f'''
                <div class="summary-banner patent" style="margin-top: 16px;">
                    <p class="summary-question">Patent Analysis Summary</p>
                    <p style="color: var(--text-muted); font-size: 13px; margin-top: 8px;">{executive}</p>
                    {f'<p style="color: var(--text-secondary); font-size: 12px; margin-top: 8px;">{business}</p>' if business else ""}
                </div>
                '''
        
        return f"""
        <div class="section">
            <div class="section-header">
                <div class="section-icon patent">🛡️</div>
                <div>
                    <h2 class="section-title">IP & Patent Analysis</h2>
                    <p class="section-subtitle">Patent Landscape — FTO assessment & IP strategy</p>
                </div>
            </div>
            
            {summary_html}
            {overview_html}
            {actions_html}
            {layers_html}
        </div>
        """
    
    def _render_exim_section(self, data: Dict) -> str:
        """Render EXIM Trade section - handles actual agent data structure"""
        exim = data.get("exim", {})
        if not exim:
            return ""
        
        actual_data = exim.get("data", exim)
        
        # Summary banner from actual agent data
        summary = actual_data.get("summary", {})
        summary_html = ""
        if summary:
            answer = summary.get("answer", "Stable")
            answer_class = "positive" if answer in ["Yes", "Active"] else "neutral" if answer == "Stable" else "negative"
            explainers = summary.get("explainers", [])
            explainers_html = " ".join([f'<span class="summary-explainer">{e}</span>' for e in explainers])
            
            summary_html = f"""
            <div class="summary-banner exim">
                <p class="summary-question">{summary.get('researcherQuestion', 'Is there active export trade?')}</p>
                <p class="summary-answer {answer_class}">{answer}</p>
                <div class="summary-explainers">{explainers_html}</div>
            </div>
            """
        
        # Trade volume table from actual trade_data
        trade_data = actual_data.get("trade_data", {})
        trade_html = ""
        if trade_data and trade_data.get("rows"):
            rows_html = ""
            for row in trade_data["rows"][:10]:  # Top 10 countries
                country = row.get("Country", "Unknown")
                current_val = row.get("2024 - 2025", "N/A")
                previous_val = row.get("2023 - 2024", "N/A")
                share = row.get("%Share", "N/A")
                growth = row.get("%Growth", "0")
                
                growth_color = "var(--success)" if float(growth or 0) > 0 else "var(--danger)" if float(growth or 0) < 0 else "var(--text-muted)"
                rows_html += f'''
                <tr>
                    <td>{country}</td>
                    <td>${current_val}M</td>
                    <td>${previous_val}M</td>
                    <td>{share}%</td>
                    <td style="color: {growth_color}; font-weight: 600;">{growth}%</td>
                </tr>
                '''
            trade_html = f'''
            <div class="data-table-container">
                <p class="data-table-title">Export Trade Volume by Country</p>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Country</th>
                            <th>2024-25</th>
                            <th>2023-24</th>
                            <th>Share</th>
                            <th>Growth</th>
                        </tr>
                    </thead>
                    <tbody>{rows_html}</tbody>
                </table>
            </div>
            '''
        
        # Analysis summary from actual data
        analysis = actual_data.get("analysis", {})
        analysis_html = ""
        if analysis and analysis.get("summary"):
            summary_data = analysis["summary"]
            total_val = summary_data.get("total_current_year", 0)
            growth = summary_data.get("overall_growth", 0)
            top_partner = summary_data.get("top_partner", "N/A")
            
            metrics = []
            metrics.append(f'''<div class="metric-card"><p class="metric-label">Total Trade Value</p><p class="metric-value">${total_val:,.1f}<span class="metric-unit">M</span></p></div>''')
            metrics.append(f'''<div class="metric-card"><p class="metric-label">YoY Growth</p><p class="metric-value">{growth:+.1f}<span class="metric-unit">%</span></p></div>''')
            metrics.append(f'''<div class="metric-card"><p class="metric-label">Top Partner</p><p class="metric-value" style="font-size: 16px;">{top_partner}</p></div>''')
            
            analysis_html = f'<div class="metrics-grid">{"".join(metrics)}</div>'
        
        # LLM insights if available
        insights = actual_data.get("llm_insights", {})
        insights_html = ""
        if insights:
            desc = insights.get("trade_volume_description", "")
            if desc:
                insights_html = f'''
                <div class="summary-banner exim" style="margin-top: 16px;">
                    <p class="summary-question">Trade Intelligence Insights</p>
                    <p style="color: var(--text-muted); font-size: 13px; margin-top: 8px;">{desc[:500]}...</p>
                </div>
                '''
        
        return f"""
        <div class="section">
            <div class="section-header">
                <div class="section-icon exim">🌍</div>
                <div>
                    <h2 class="section-title">Trade & Supply Chain</h2>
                    <p class="section-subtitle">EXIM Analysis — Export-import trends & sourcing intelligence</p>
                </div>
            </div>
            
            {summary_html}
            {analysis_html}
            {trade_html}
            {insights_html}
        </div>
        """
    
    def _render_internal_section(self, data: Dict) -> str:
        """Render Internal Knowledge section - handles actual agent data structure"""
        internal = data.get("internal_knowledge", {})
        if not internal:
            return ""
        
        actual_data = internal.get("data", internal)
        
        # Summary banner from actual agent data
        summary = actual_data.get("summary", {})
        summary_html = ""
        if summary and summary.get("researcherQuestion"):
            answer = summary.get("answer", "Yes")
            answer_class = "positive" if answer in ["Yes", "Strong"] else "neutral"
            explainers = summary.get("explainers", [])
            explainers_html = " ".join([f'<span class="summary-explainer">{e}</span>' for e in explainers])
            
            summary_html = f"""
            <div class="summary-banner internal">
                <p class="summary-question">{summary.get('researcherQuestion', 'Does internal knowledge support this research?')}</p>
                <p class="summary-answer {answer_class}">{answer}</p>
                <div class="summary-explainers">{explainers_html}</div>
            </div>
            """
        
        # Overview section
        overview = actual_data.get("overview", "")
        analysis = actual_data.get("analysis", {})
        if not overview and analysis:
            overview = analysis.get("overview", "")
        
        overview_html = ""
        if overview:
            overview_html = f"""
            <div class="chart-container">
                <p class="chart-title">Strategic Overview</p>
                <p style="font-size: 13px; color: var(--text); line-height: 1.6;">{overview[:800]}{"..." if len(overview) > 800 else ""}</p>
            </div>
            """
        
        # Key findings
        key_findings = actual_data.get("key_findings", [])
        if not key_findings and analysis:
            key_findings = analysis.get("key_findings", [])
        
        findings_html = ""
        if key_findings:
            items = ""
            for i, finding in enumerate(key_findings[:5], 1):  # Top 5 findings
                items += f'''
                <div class="metric-card" style="min-width: 100%; margin-bottom: 12px;">
                    <p class="metric-label">Finding #{i}</p>
                    <p style="font-size: 13px; color: var(--text); line-height: 1.5;">{finding[:300]}{"..." if len(finding) > 300 else ""}</p>
                </div>
                '''
            findings_html = f'''
            <div class="chart-container">
                <p class="chart-title">Key Findings from Internal Analysis</p>
                <div style="display: flex; flex-direction: column;">{items}</div>
            </div>
            '''
        
        # Recommendations
        recommendations = actual_data.get("recommendations", [])
        if not recommendations and analysis:
            recommendations = analysis.get("recommendations", [])
        
        recommendations_html = ""
        if recommendations:
            items = ""
            for rec in recommendations[:3]:  # Top 3 recommendations
                items += f'<li style="margin-bottom: 8px; color: var(--text); font-size: 13px;">{rec}</li>'
            recommendations_html = f'''
            <div class="summary-banner internal" style="margin-top: 16px;">
                <p class="summary-question">Strategic Recommendations</p>
                <ul style="margin-top: 12px; padding-left: 20px;">{items}</ul>
            </div>
            '''
        
        # Strategic implications
        implications = actual_data.get("strategic_implications", "")
        if not implications and analysis:
            implications = analysis.get("strategic_implications", "")
        
        implications_html = ""
        if implications:
            implications_html = f'''
            <div class="chart-container" style="margin-top: 16px;">
                <p class="chart-title">Strategic Implications</p>
                <p style="font-size: 13px; color: var(--text); line-height: 1.6;">{implications[:600]}{"..." if len(implications) > 600 else ""}</p>
            </div>
            '''
        
        # Internal references
        references = actual_data.get("internal_references", [])
        if not references and analysis:
            references = analysis.get("internal_references", [])
        
        references_html = ""
        if references:
            ref_items = ""
            for ref in references[:4]:
                ref_items += f'<span class="summary-explainer" style="display: inline-block; margin: 4px;">📄 {ref}</span>'
            references_html = f'''
            <div style="margin-top: 16px; padding: 12px; background: var(--section-bg); border-radius: 8px;">
                <p style="font-size: 12px; color: var(--text-muted); margin-bottom: 8px;">Data Sources</p>
                {ref_items}
            </div>
            '''
        
        return f"""
        <div class="section">
            <div class="section-header">
                <div class="section-icon internal">📚</div>
                <div>
                    <h2 class="section-title">Internal Knowledge</h2>
                    <p class="section-subtitle">Company Intelligence — Prior research & strategic insights</p>
                </div>
            </div>
            
            {summary_html}
            {overview_html}
            {findings_html}
            {implications_html}
            {recommendations_html}
            {references_html}
        </div>
        """
    
    def _render_web_intel_section(self, data: Dict) -> str:
        """Render Web Intelligence section - handles actual agent data structure"""
        web = data.get("web_intelligence", {})
        if not web:
            return ""
        
        actual_data = web.get("data", web)
        
        # Summary banner
        summary = actual_data.get("summary", {})
        summary_html = ""
        if summary and summary.get("researcherQuestion"):
            answer = summary.get("answer", "Neutral")
            answer_class = "positive" if answer in ["Positive", "Favorable"] else "neutral" if answer in ["Neutral", "Mixed"] else "negative"
            explainers = summary.get("explainers", [])
            explainers_html = " ".join([f'<span class="summary-explainer">{e}</span>' for e in explainers])
            
            summary_html = f"""
            <div class="summary-banner web">
                <p class="summary-question">{summary.get('researcherQuestion', 'Is market sentiment favorable?')}</p>
                <p class="summary-answer {answer_class}">{answer}</p>
                <div class="summary-explainers">{explainers_html}</div>
            </div>
            """
        
        # Top signal from actual agent data
        top_signal = actual_data.get("top_signal", {})
        signal_html = ""
        if top_signal:
            score = top_signal.get("score", 0)
            label = top_signal.get("label", "MEDIUM")
            text = top_signal.get("text", "")
            why = top_signal.get("why", [])
            
            # Determine color based on label
            label_class = "high" if label == "HIGH" else "medium" if label in ["MEDIUM", "MODERATE"] else "low"
            
            why_html = ""
            if why:
                why_items = "".join([f'<li style="color: var(--text-muted); font-size: 12px; margin: 4px 0;">{w}</li>' for w in why[:4]])
                why_html = f'<ul style="margin-top: 8px; padding-left: 16px;">{why_items}</ul>'
            
            signal_html = f'''
            <div class="metrics-grid" style="margin-bottom: 16px;">
                <div class="metric-card">
                    <p class="metric-label">Signal Score</p>
                    <p class="metric-value">{score}<span class="metric-unit">/100</span></p>
                </div>
                <div class="metric-card">
                    <p class="metric-label">Signal Strength</p>
                    <p class="metric-value"><span class="badge {label_class}">{label}</span></p>
                </div>
            </div>
            <div class="chart-container">
                <p class="chart-title">Intelligence Summary</p>
                <p style="font-size: 13px; color: var(--text); white-space: pre-line;">{text[:500] if text else "No signal text available"}</p>
                {why_html}
            </div>
            '''
        
        # Sentiment summary (parse from explainers if not directly available)
        sentiment = actual_data.get("sentiment_summary", {})
        sentiment_html = ""
        if sentiment and (sentiment.get("positive") or sentiment.get("neutral") or sentiment.get("negative")):
            sentiment_html = f'''
            <div class="metrics-grid">
                <div class="metric-card">
                    <p class="metric-label">Positive</p>
                    <p class="metric-value" style="color: var(--success);">{sentiment.get("positive", 0)}<span class="metric-unit">%</span></p>
                </div>
                <div class="metric-card">
                    <p class="metric-label">Neutral</p>
                    <p class="metric-value" style="color: var(--exim);">{sentiment.get("neutral", 0)}<span class="metric-unit">%</span></p>
                </div>
                <div class="metric-card">
                    <p class="metric-label">Negative</p>
                    <p class="metric-value" style="color: var(--warning);">{sentiment.get("negative", 0)}<span class="metric-unit">%</span></p>
                </div>
            </div>
            '''
        
        # News articles from top_headlines or news_articles
        news = actual_data.get("top_headlines") or actual_data.get("news_articles") or actual_data.get("news", [])
        news_html = ""
        if news:
            items = ""
            for n in news[:4]:
                title = n.get("title", "")
                source = n.get("source", "")
                published = n.get("publishedAt", "")
                snippet = n.get("snippet", "")
                tags = n.get("tags", [])
                
                tags_html = ""
                if tags:
                    tags_html = " ".join([f'<span class="summary-explainer" style="font-size: 10px;">{t}</span>' for t in tags[:3]])
                
                items += f'''
                <div style="padding: 12px; background: rgba(6, 182, 212, 0.05); border: 1px solid rgba(6, 182, 212, 0.2); border-radius: 8px; margin-bottom: 8px;">
                    <p style="font-size: 13px; font-weight: 500; color: var(--text); margin-bottom: 4px;">{title}</p>
                    <p style="font-size: 11px; color: var(--text-muted); margin-bottom: 6px;">
                        <span style="color: var(--web);">{source}</span>
                        {f' • {published[:10]}' if published else ""}
                    </p>
                    {f'<p style="font-size: 12px; color: var(--text-muted);">{snippet[:150]}...</p>' if snippet else ''}
                    {tags_html}
                </div>
                '''
            news_html = f'''
            <div class="chart-container">
                <p class="chart-title">Recent News & Headlines ({len(news)} articles)</p>
                {items}
            </div>
            '''
        
        # Trend sparkline info if available
        sparkline = actual_data.get("trend_sparkline", {})
        trend_html = ""
        if sparkline and sparkline.get("title"):
            desc = sparkline.get("description", "")
            trend_html = f'''
            <div style="margin-top: 16px; padding: 12px; background: var(--section-bg); border-radius: 8px;">
                <p style="font-size: 14px; font-weight: 600; color: var(--text);">📈 {sparkline.get("title")}</p>
                <p style="font-size: 12px; color: var(--text-muted);">{desc}</p>
            </div>
            '''
        
        # Confidence
        confidence = actual_data.get("confidence", "MEDIUM")
        confidence_class = {"HIGH": "low", "MEDIUM": "medium", "LOW": "high"}.get(confidence, "medium")
        
        return f"""
        <div class="section">
            <div class="section-header">
                <div class="section-icon web">🌐</div>
                <div>
                    <h2 class="section-title">External Intelligence</h2>
                    <p class="section-subtitle">Web Intelligence — News, sentiment & market buzz</p>
                </div>
            </div>
            
            {summary_html}
            {signal_html}
            {sentiment_html}
            {news_html}
            {trend_html}
            
            <div style="text-align: right; margin-top: 16px;">
                <span class="badge {confidence_class}">Confidence: {confidence}</span>
            </div>
        </div>
        """
    
    def _render_bar_chart(self, title: str, data: List[Dict], x_field: str, y_field: str, color: str = "#3b82f6") -> str:
        """Render a simple SVG bar chart"""
        if not data:
            return ""
        
        # Calculate dimensions
        width = 600
        height = 300
        margin = {"top": 20, "right": 30, "bottom": 60, "left": 60}
        chart_width = width - margin["left"] - margin["right"]
        chart_height = height - margin["top"] - margin["bottom"]
        
        # Get max value
        max_val = max(d.get(y_field, 0) for d in data)
        if max_val == 0:
            max_val = 1
        
        # Bar width
        bar_width = chart_width / len(data) * 0.7
        bar_gap = chart_width / len(data) * 0.15
        
        bars = ""
        labels = ""
        values = ""
        
        for i, d in enumerate(data):
            x = margin["left"] + i * (chart_width / len(data)) + bar_gap
            val = d.get(y_field, 0)
            bar_height = (val / max_val) * chart_height
            y = margin["top"] + chart_height - bar_height
            
            # Gradient
            bars += f'''
            <rect x="{x}" y="{y}" width="{bar_width}" height="{bar_height}" 
                  fill="{color}" rx="4" opacity="0.9"/>
            '''
            
            # X-axis label
            labels += f'''
            <text x="{x + bar_width/2}" y="{height - 20}" 
                  class="label" text-anchor="middle">{d.get(x_field, "")}</text>
            '''
            
            # Value label
            values += f'''
            <text x="{x + bar_width/2}" y="{y - 5}" 
                  class="value-label" text-anchor="middle">${val}B</text>
            '''
        
        return f'''
        <div class="chart-container">
            <p class="chart-title">{title}</p>
            <svg class="chart-svg" viewBox="0 0 {width} {height}">
                <!-- Grid lines -->
                <line x1="{margin["left"]}" y1="{margin["top"]}" 
                      x2="{margin["left"]}" y2="{margin["top"] + chart_height}" 
                      class="axis-line"/>
                <line x1="{margin["left"]}" y1="{margin["top"] + chart_height}" 
                      x2="{width - margin["right"]}" y2="{margin["top"] + chart_height}" 
                      class="axis-line"/>
                
                {bars}
                {labels}
                {values}
            </svg>
        </div>
        '''
    
    def _render_pie_chart(self, title: str, data: List[Dict], label_field: str, value_field: str) -> str:
        """Render a simple SVG donut chart"""
        if not data:
            return ""
        
        # Parse share values
        def parse_share(share):
            if isinstance(share, (int, float)):
                return float(share)
            return float(str(share).replace("%", "").replace("~", "").strip() or 0)
        
        parsed_data = [(d.get(label_field, ""), parse_share(d.get(value_field, 0))) for d in data]
        total = sum(v for _, v in parsed_data)
        if total == 0:
            total = 1
        
        # SVG dimensions
        cx, cy = 120, 120
        outer_r = 100
        inner_r = 60
        
        # Generate pie slices
        slices = ""
        legend_items = ""
        start_angle = -90  # Start from top
        
        for i, (label, value) in enumerate(parsed_data):
            pct = value / total
            angle = pct * 360
            
            # Calculate arc
            end_angle = start_angle + angle
            large_arc = 1 if angle > 180 else 0
            
            # Convert to radians
            import math
            start_rad = math.radians(start_angle)
            end_rad = math.radians(end_angle)
            
            # Outer arc points
            x1 = cx + outer_r * math.cos(start_rad)
            y1 = cy + outer_r * math.sin(start_rad)
            x2 = cx + outer_r * math.cos(end_rad)
            y2 = cy + outer_r * math.sin(end_rad)
            
            # Inner arc points
            x3 = cx + inner_r * math.cos(end_rad)
            y3 = cy + inner_r * math.sin(end_rad)
            x4 = cx + inner_r * math.cos(start_rad)
            y4 = cy + inner_r * math.sin(start_rad)
            
            color = self.CHART_COLORS[i % len(self.CHART_COLORS)]
            
            path = f"M {x1} {y1} A {outer_r} {outer_r} 0 {large_arc} 1 {x2} {y2} L {x3} {y3} A {inner_r} {inner_r} 0 {large_arc} 0 {x4} {y4} Z"
            slices += f'<path d="{path}" fill="{color}" stroke="var(--card)" stroke-width="2"/>'
            
            legend_items += f'''
            <div class="donut-legend-item">
                <div class="donut-legend-color" style="background: {color};"></div>
                <span class="donut-legend-label">{label}</span>
                <span class="donut-legend-value">{value:.0f}%</span>
            </div>
            '''
            
            start_angle = end_angle
        
        return f'''
        <div class="chart-container">
            <p class="chart-title">{title}</p>
            <div class="donut-chart-container">
                <svg width="240" height="240" viewBox="0 0 240 240">
                    {slices}
                </svg>
                <div class="donut-legend">
                    {legend_items}
                </div>
            </div>
        </div>
        '''
    
    def _render_footer(self) -> str:
        """Render report footer"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""
        <div class="report-footer">
            <p><strong>PharmAssist Intelligence Platform</strong></p>
            <p>Generated: {now} | Multi-Agent Analysis System v1.0</p>
            <p>This report is confidential and intended for authorized recipients only.</p>
        </div>
        """
    
    def generate(self, data: Dict) -> str:
        """
        Generate complete HTML report from agent data.
        
        Args:
            data: Dictionary containing all agent data and metadata
            
        Returns:
            Complete HTML string for the report
        """
        drug_name = data.get("drug_name", data.get("drug", "Unknown Drug"))
        indication = data.get("indication", data.get("disease", "Unknown Indication"))
        report_date = data.get("report_date", datetime.now().strftime("%B %d, %Y"))
        
        # Build HTML
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pharmaceutical Intelligence Report — {drug_name}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700;800&family=DM+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        {self.css}
    </style>
</head>
<body>
    <div class="report-container">
        {self._render_cover_page(drug_name, indication, report_date)}
        {self._render_executive_summary(data)}
        {self._render_iqvia_section(data)}
        {self._render_clinical_section(data)}
        
        <div class="page-break"></div>
        
        {self._render_patent_section(data)}
        {self._render_exim_section(data)}
        
        <div class="page-break"></div>
        
        {self._render_internal_section(data)}
        {self._render_web_intel_section(data)}
        
        {self._render_footer()}
    </div>
</body>
</html>
        """
        
        return html
    
    def generate_from_agents_data(self, agents_data: Dict, drug_name: str, indication: str) -> str:
        """
        Generate report from raw agents data dictionary.
        
        Args:
            agents_data: Dictionary with agent keys (iqvia, clinical, etc.)
            drug_name: Name of the drug
            indication: Target indication
            
        Returns:
            Complete HTML string
        """
        from ..report_schema import (
            parse_agent_data_from_dict,
            compute_opportunity_score,
            generate_key_takeaways,
            generate_recommendation
        )
        
        # Prepare data
        data = {
            "drug_name": drug_name,
            "indication": indication,
            **agents_data
        }
        
        # Parse and compute metrics
        schema = parse_agent_data_from_dict(data)
        score = compute_opportunity_score(schema)
        takeaways = generate_key_takeaways(schema)
        recommendation = generate_recommendation(schema, score)
        
        # Add computed values
        data["opportunity_score"] = score
        data["key_takeaways"] = takeaways
        data["recommendation"] = recommendation
        
        return self.generate(data)
