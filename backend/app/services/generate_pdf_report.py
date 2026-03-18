"""
PDF Report Generator Tool
Generates comprehensive pharmaceutical intelligence reports with charts and tables
"""

# Conditional import for CrewAI tool decorator
try:
    from crewai.tools import tool
    HAS_CREWAI = True
except ImportError:
    HAS_CREWAI = False
    # Create a dummy decorator for standalone usage
    def tool(name):
        def decorator(func):
            return func
        return decorator

# Check for required PDF generation dependencies
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
        PageBreak, Image, KeepTogether
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor
    HAS_REPORTLAB = True
except ImportError as e:
    HAS_REPORTLAB = False
    REPORTLAB_ERROR = str(e)

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-GUI backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    HAS_MATPLOTLIB = True
except ImportError as e:
    HAS_MATPLOTLIB = False
    MATPLOTLIB_ERROR = str(e)

from datetime import datetime
import io
import os
from typing import Dict, Any, List
import json


# Check if all required dependencies are available
def check_dependencies():
    """Check if all required dependencies are installed"""
    missing = []
    if not HAS_REPORTLAB:
        missing.append(f"reportlab - {REPORTLAB_ERROR}")
    if not HAS_MATPLOTLIB:
        missing.append(f"matplotlib - {MATPLOTLIB_ERROR}")
    
    if missing:
        error_msg = "Missing required dependencies:\n" + "\n".join(f"  - {dep}" for dep in missing)
        error_msg += "\n\nInstall with: pip install reportlab matplotlib Pillow"
        return False, error_msg
    return True, None


class PDFReportGenerator:
    """Generate professional pharmaceutical intelligence reports"""
    
    # Enhanced color scheme with gradients and modern palette
    COLORS = {
        'primary': HexColor('#1e40af'),      # Deep Blue
        'primary_light': HexColor('#3b82f6'), # Light Blue
        'secondary': HexColor('#7c3aed'),    # Deep Purple
        'secondary_light': HexColor('#a78bfa'), # Light Purple
        'accent': HexColor('#059669'),       # Deep Green
        'accent_light': HexColor('#10b981'), # Light Green
        'warning': HexColor('#d97706'),      # Deep Amber
        'warning_light': HexColor('#f59e0b'), # Light Amber
        'danger': HexColor('#dc2626'),       # Deep Red
        'danger_light': HexColor('#ef4444'), # Light Red
        'cyan': HexColor('#0891b2'),         # Deep Cyan
        'cyan_light': HexColor('#06b6d4'),   # Light Cyan
        'dark': HexColor('#18181b'),         # Dark zinc
        'light': HexColor('#f4f4f5'),        # Light zinc
        'lighter': HexColor('#fafafa'),      # Very light
        'text': HexColor('#1f2937'),         # Dark text
        'text_light': HexColor('#6b7280'),   # Gray text
        'border': HexColor('#e5e7eb'),       # Light border
    }
    
    def __init__(self, filename: str):
        self.filename = filename
        self.doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch
        )
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self.story = []
        self.chart_counter = 0
        
    def _setup_custom_styles(self):
        """Setup custom paragraph styles with enhanced formatting"""
        # Title style with shadow effect
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=28,
            textColor=self.COLORS['primary'],
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=34
        ))
        
        # Section header with bottom border
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=18,
            textColor=self.COLORS['primary'],
            spaceAfter=16,
            spaceBefore=24,
            fontName='Helvetica-Bold',
            borderWidth=2,
            borderColor=self.COLORS['primary_light'],
            borderPadding=8,
            leftIndent=0,
            backColor=self.COLORS['lighter']
        ))
        
        # Subsection header with accent
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=self.COLORS['secondary'],
            spaceAfter=10,
            spaceBefore=14,
            fontName='Helvetica-Bold',
            leftIndent=10,
            borderWidth=0,
            borderPadding=4,
            backColor=HexColor('#f3f4f6')
        ))
        
        # Body text with better readability
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=10,
            leading=16,
            textColor=self.COLORS['text'],
            wordWrap='CJK'  # Enable word wrapping
        ))
        
        # Bullet points with better formatting
        self.styles.add(ParagraphStyle(
            name='CustomBullet',
            parent=self.styles['BodyText'],
            fontSize=10,
            leftIndent=24,
            rightIndent=20,  # Add right margin
            spaceAfter=8,
            bulletIndent=12,
            leading=15,
            textColor=self.COLORS['text'],
            wordWrap='CJK',  # Enable word wrapping
            alignment=TA_LEFT  # Left align for better wrapping
        ))
        
        # Highlight box style
        self.styles.add(ParagraphStyle(
            name='HighlightBox',
            parent=self.styles['BodyText'],
            fontSize=11,
            backColor=self.COLORS['lighter'],
            borderWidth=1,
            borderColor=self.COLORS['border'],
            borderPadding=12,
            spaceAfter=12,
            leading=16
        ))
        
        # Key insight style
        self.styles.add(ParagraphStyle(
            name='KeyInsight',
            parent=self.styles['BodyText'],
            fontSize=10,
            leftIndent=16,
            rightIndent=16,
            backColor=HexColor('#eff6ff'),
            borderWidth=2,
            borderColor=self.COLORS['primary_light'],
            borderPadding=10,
            spaceAfter=10,
            leading=14,
            wordWrap='CJK'  # Enable word wrapping
        ))
        
    def add_cover_page(self, drug_name: str, indication: str, date: str = None):
        """Add enhanced cover page with better visual design"""
        if date is None:
            date = datetime.now().strftime("%B %d, %Y")
            
        self.story.append(Spacer(1, 1.5*inch))
        
        # Decorative top line
        line_style = [
            ('LINEBELOW', (0, 0), (-1, 0), 3, self.COLORS['primary']),
            ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['lighter'])
        ]
        top_line = Table([['  ']], colWidths=[6.5*inch])
        top_line.setStyle(TableStyle(line_style))
        self.story.append(top_line)
        self.story.append(Spacer(1, 0.4*inch))
        
        # Title with gradient effect
        title = Paragraph(
            f"<b>PHARMACEUTICAL</b><br/><b>INTELLIGENCE REPORT</b>",
            ParagraphStyle(
                name='CoverTitle',
                fontSize=30,
                textColor=self.COLORS['primary'],
                alignment=TA_CENTER,
                fontName='Helvetica-Bold',
                leading=36,
                spaceAfter=0
            )
        )
        self.story.append(title)
        self.story.append(Spacer(1, 0.5*inch))
        
        # Drug name in colored box
        drug_box_data = [[Paragraph(
            f"<b>{drug_name.upper()}</b>",
            ParagraphStyle(
                name='DrugTitle',
                fontSize=24,
                textColor=colors.white,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
        )]]
        drug_box = Table(drug_box_data, colWidths=[5*inch])
        drug_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.COLORS['secondary']),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 16),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
            ('LEFTPADDING', (0, 0), (-1, -1), 20),
            ('RIGHTPADDING', (0, 0), (-1, -1), 20),
        ]))
        self.story.append(drug_box)
        self.story.append(Spacer(1, 0.3*inch))
        
        # Indication with icon
        indication_text = Paragraph(
            f"<font color='#{self.COLORS['accent'].hexval()[2:]}'><b>◆</b></font> <i>{indication.upper() if indication != 'general' else 'COMPREHENSIVE ANALYSIS'}</i>",
            ParagraphStyle(
                name='Indication',
                fontSize=16,
                textColor=self.COLORS['text'],
                alignment=TA_CENTER,
                fontName='Helvetica-Oblique',
                spaceAfter=0
            )
        )
        self.story.append(indication_text)
        self.story.append(Spacer(1, 1.2*inch))
        
        # Info box with date and platform
        info_data = [
            [Paragraph(f"<b>Report Date:</b> {date}", 
                      ParagraphStyle(name='InfoText', fontSize=11, alignment=TA_CENTER))],
            [Paragraph("<b>Generated by:</b> PharmAssist Intelligence Platform", 
                      ParagraphStyle(name='InfoText2', fontSize=11, alignment=TA_CENTER))],
            [Paragraph("<b>Multi-Agent Analysis System</b>", 
                      ParagraphStyle(name='InfoText3', fontSize=10, alignment=TA_CENTER, textColor=self.COLORS['text_light']))]
        ]
        info_box = Table(info_data, colWidths=[5*inch])
        info_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.COLORS['lighter']),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('BOX', (0, 0), (-1, -1), 1, self.COLORS['border']),
        ]))
        self.story.append(info_box)
        
        # Decorative bottom line
        self.story.append(Spacer(1, 0.3*inch))
        bottom_line = Table([['  ']], colWidths=[6.5*inch])
        bottom_line.setStyle(TableStyle(line_style))
        self.story.append(bottom_line)
        
        self.story.append(PageBreak())
        
    def add_executive_summary(self, summary_data: Dict[str, Any]):
        """Add executive summary section"""
        self.story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        self.story.append(Spacer(1, 0.2*inch))
        
        if isinstance(summary_data, dict) and 'sections' in summary_data:
            for section in summary_data.get('sections', []):
                bullet = Paragraph(
                    f"• <b>{section.get('title', 'Section')}:</b> {section.get('description', 'N/A')}",
                    self.styles['CustomBullet']
                )
                self.story.append(bullet)
                self.story.append(Spacer(1, 0.05*inch))
        
        self.story.append(Spacer(1, 0.3*inch))
        
    def add_market_analysis(self, iqvia_data: Dict[str, Any], indication: str):
        """Add IQVIA market analysis section with charts"""
        self.story.append(Paragraph("Market Analysis", self.styles['SectionHeader']))
        self.story.append(Spacer(1, 0.15*inch))
        
        if indication == "general":
            # Market forecast chart
            if 'market_forecast' in iqvia_data:
                forecast = iqvia_data['market_forecast']
                self.story.append(Paragraph(
                    forecast.get('title', 'Market Forecast'),
                    self.styles['SubsectionHeader']
                ))
                
                # Create chart
                chart_img = self._create_market_forecast_chart(forecast.get('data', []))
                if chart_img:
                    self.story.append(chart_img)
                
                # Description
                if 'description' in forecast:
                    self.story.append(Spacer(1, 0.1*inch))
                    self.story.append(Paragraph(
                        forecast['description'],
                        self.styles['CustomBody']
                    ))
                
                self.story.append(Spacer(1, 0.2*inch))
            
            # Competitive share
            if 'competitive_share' in iqvia_data:
                comp_share = iqvia_data['competitive_share']
                self.story.append(Paragraph(
                    comp_share.get('title', 'Competitive Share'),
                    self.styles['SubsectionHeader']
                ))
                
                # Create table
                if 'data' in comp_share:
                    table_data = [['Company', 'Market Share']]
                    for item in comp_share['data']:
                        table_data.append([
                            item.get('company', ''),
                            item.get('share', '')
                        ])
                    
                    table = Table(table_data, colWidths=[3.5*inch, 2*inch])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['primary']),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 11),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('TEXTCOLOR', (0, 1), (-1, -1), self.COLORS['text']),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 10),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.COLORS['light']]),
                    ]))
                    self.story.append(table)
                
                if 'description' in comp_share:
                    self.story.append(Spacer(1, 0.1*inch))
                    self.story.append(Paragraph(
                        comp_share['description'],
                        self.styles['CustomBody']
                    ))
        else:
            # AUD-specific market data
            if 'market_overview' in iqvia_data:
                overview = iqvia_data['market_overview']
                self.story.append(Paragraph(
                    overview.get('title', 'Market Overview'),
                    self.styles['SubsectionHeader']
                ))
                
                if 'metrics' in overview:
                    table_data = [['Metric', 'Value']]
                    for metric in overview['metrics']:
                        table_data.append([
                            metric.get('label', ''),
                            metric.get('value', '')
                        ])
                    
                    table = Table(table_data, colWidths=[3.5*inch, 2*inch])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['accent']),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 11),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('TEXTCOLOR', (0, 1), (-1, -1), self.COLORS['text']),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 10),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.COLORS['light']]),
                    ]))
                    self.story.append(table)
                    self.story.append(Spacer(1, 0.2*inch))
            
            # Existing therapies
            if 'existing_therapies' in iqvia_data:
                therapies = iqvia_data['existing_therapies']
                self.story.append(Paragraph(
                    therapies.get('title', 'Existing Therapies'),
                    self.styles['SubsectionHeader']
                ))
                
                if 'data' in therapies:
                    table_data = [['Drug', 'Mechanism', 'Efficacy', 'Limitations']]
                    for therapy in therapies['data']:
                        table_data.append([
                            therapy.get('drug', ''),
                            therapy.get('mechanism', ''),
                            therapy.get('efficacy', ''),
                            therapy.get('limitations', '')
                        ])
                    
                    table = Table(table_data, colWidths=[1.3*inch, 1.8*inch, 1*inch, 2.4*inch])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['secondary']),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('TEXTCOLOR', (0, 1), (-1, -1), self.COLORS['text']),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.COLORS['light']]),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]))
                    self.story.append(table)
        
        self.story.append(Spacer(1, 0.3*inch))
        
    def add_clinical_analysis(self, clinical_data: Dict[str, Any], indication: str):
        """Add clinical trials analysis section"""
        self.story.append(PageBreak())
        self.story.append(Paragraph("Clinical Evidence", self.styles['SectionHeader']))
        self.story.append(Spacer(1, 0.15*inch))
        
        if indication == "general":
            # Phase distribution
            if 'phase_distribution' in clinical_data:
                phase_dist = clinical_data['phase_distribution']
                self.story.append(Paragraph(
                    phase_dist.get('title', 'Phase Distribution'),
                    self.styles['SubsectionHeader']
                ))
                
                # Create pie chart
                chart_img = self._create_phase_distribution_chart(phase_dist.get('data', []))
                if chart_img:
                    self.story.append(chart_img)
                
                if 'description' in phase_dist:
                    self.story.append(Spacer(1, 0.1*inch))
                    self.story.append(Paragraph(
                        phase_dist['description'],
                        self.styles['CustomBody']
                    ))
                
                self.story.append(Spacer(1, 0.2*inch))
            
            # Sponsor profile
            if 'sponsor_profile' in clinical_data:
                sponsor = clinical_data['sponsor_profile']
                self.story.append(Paragraph(
                    sponsor.get('title', 'Sponsor Profile'),
                    self.styles['SubsectionHeader']
                ))
                
                if 'data' in sponsor:
                    table_data = [['Sponsor', 'Trial Count', 'Primary Focus']]
                    for item in sponsor['data']:
                        table_data.append([
                            item.get('sponsor', ''),
                            f"~{item.get('trial_count', '')}",
                            item.get('focus', '')
                        ])
                    
                    table = Table(table_data, colWidths=[2.5*inch, 1.5*inch, 2.5*inch])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['accent']),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 11),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('TEXTCOLOR', (0, 1), (-1, -1), self.COLORS['text']),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 10),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.COLORS['light']]),
                    ]))
                    self.story.append(table)
        else:
            # AUD-specific clinical data
            if 'key_trials' in clinical_data:
                trials = clinical_data['key_trials']
                self.story.append(Paragraph(
                    trials.get('title', 'Key Trials'),
                    self.styles['SubsectionHeader']
                ))
                
                if 'data' in trials:
                    table_data = [['Trial ID', 'Phase', 'Primary Endpoints', 'Sponsor']]
                    for trial in trials['data']:
                        table_data.append([
                            trial.get('trial_id', ''),
                            trial.get('phase', ''),
                            trial.get('primary_endpoints', ''),
                            trial.get('sponsor', '')
                        ])
                    
                    table = Table(table_data, colWidths=[1.2*inch, 0.8*inch, 2.8*inch, 1.7*inch])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['accent']),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('TEXTCOLOR', (0, 1), (-1, -1), self.COLORS['text']),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 8),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.COLORS['light']]),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]))
                    self.story.append(table)
                    
                    if 'description' in trials:
                        self.story.append(Spacer(1, 0.1*inch))
                        self.story.append(Paragraph(
                            trials['description'],
                            self.styles['CustomBody']
                        ))
        
        self.story.append(Spacer(1, 0.3*inch))
        
    def add_patent_analysis(self, patent_data: Dict[str, Any], indication: str):
        """Add patent landscape analysis"""
        self.story.append(PageBreak())
        self.story.append(Paragraph("Patent Landscape", self.styles['SectionHeader']))
        self.story.append(Spacer(1, 0.15*inch))
        
        if indication == "general":
            # Landscape overview
            if 'landscape_overview' in patent_data:
                overview = patent_data['landscape_overview']
                self.story.append(Paragraph(
                    overview.get('title', 'Landscape Overview'),
                    self.styles['SubsectionHeader']
                ))
                
                if 'sections' in overview:
                    for section in overview['sections']:
                        bullet = Paragraph(
                            f"• <b>{section.get('label', '')}:</b> {section.get('value', '')}",
                            self.styles['CustomBullet']
                        )
                        self.story.append(bullet)
                
                if 'description' in overview:
                    self.story.append(Spacer(1, 0.1*inch))
                    self.story.append(Paragraph(
                        overview['description'],
                        self.styles['CustomBody']
                    ))
                
                self.story.append(Spacer(1, 0.2*inch))
            
            # Filing heatmap
            if 'filing_heatmap' in patent_data:
                heatmap = patent_data['filing_heatmap']
                self.story.append(Paragraph(
                    heatmap.get('title', 'Filing Activity'),
                    self.styles['SubsectionHeader']
                ))
                
                if 'data' in heatmap:
                    table_data = [['Region', 'Filing Count']]
                    for item in heatmap['data']:
                        table_data.append([
                            item.get('region', ''),
                            str(item.get('count', ''))
                        ])
                    
                    table = Table(table_data, colWidths=[3.5*inch, 2*inch])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['warning']),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 11),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('TEXTCOLOR', (0, 1), (-1, -1), self.COLORS['text']),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 10),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.COLORS['light']]),
                    ]))
                    self.story.append(table)
        else:
            # AUD-specific patent data
            if 'aud_focus' in patent_data:
                aud_focus = patent_data['aud_focus']
                self.story.append(Paragraph(
                    aud_focus.get('title', 'AUD Patent Focus'),
                    self.styles['SubsectionHeader']
                ))
                
                if 'sections' in aud_focus:
                    for section in aud_focus['sections']:
                        bullet = Paragraph(
                            f"• <b>{section.get('label', '')}:</b> {section.get('value', '')}",
                            self.styles['CustomBullet']
                        )
                        self.story.append(bullet)
                
                if 'description' in aud_focus:
                    self.story.append(Spacer(1, 0.1*inch))
                    self.story.append(Paragraph(
                        aud_focus['description'],
                        self.styles['CustomBody']
                    ))
        
        self.story.append(Spacer(1, 0.3*inch))
        
    def add_exim_analysis(self, exim_data: Dict[str, Any]):
        """Add EXIM trade analysis"""
        self.story.append(PageBreak())
        self.story.append(Paragraph("Export-Import Trade Analysis", self.styles['SectionHeader']))
        self.story.append(Spacer(1, 0.15*inch))
        
        # Trade volume
        if 'trade_volume' in exim_data:
            trade = exim_data['trade_volume']
            self.story.append(Paragraph(
                trade.get('title', 'Trade Volume'),
                self.styles['SubsectionHeader']
            ))
            
            if 'data' in trade:
                table_data = [['Source Country', 'Q2 2024 (kg)', 'Q3 2024 (kg)', 'QoQ Growth']]
                for item in trade['data']:
                    table_data.append([
                        item.get('country', ''),
                        item.get('q2_2024', ''),
                        item.get('q3_2024', ''),
                        item.get('qoq_growth', '')
                    ])
                
                table = Table(table_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['cyan']),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('TEXTCOLOR', (0, 1), (-1, -1), self.COLORS['text']),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.COLORS['light']]),
                ]))
                self.story.append(table)
            
            if 'description' in trade:
                self.story.append(Spacer(1, 0.1*inch))
                self.story.append(Paragraph(
                    trade['description'],
                    self.styles['CustomBody']
                ))
            
            self.story.append(Spacer(1, 0.2*inch))
        
        # Import dependency
        if 'import_dependency' in exim_data:
            dependency = exim_data['import_dependency']
            self.story.append(Paragraph(
                dependency.get('title', 'Import Dependency'),
                self.styles['SubsectionHeader']
            ))
            
            if 'data' in dependency:
                table_data = [['Region', 'Dependency %', 'Primary Sources', 'Risk Level']]
                for item in dependency['data']:
                    table_data.append([
                        item.get('region', ''),
                        item.get('dependency_percent', ''),
                        item.get('primary_sources', ''),
                        item.get('risk_level', '')
                    ])
                
                table = Table(table_data, colWidths=[1.5*inch, 1.2*inch, 2.3*inch, 1.5*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['warning']),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                    ('ALIGN', (3, 0), (3, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('TEXTCOLOR', (0, 1), (-1, -1), self.COLORS['text']),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.COLORS['light']]),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                self.story.append(table)
        
        self.story.append(Spacer(1, 0.3*inch))
        
    def add_internal_knowledge(self, internal_data: Dict[str, Any]):
        """Add internal knowledge insights with enhanced formatting"""
        self.story.append(PageBreak())
        self.story.append(Paragraph("Strategic Insights", self.styles['SectionHeader']))
        self.story.append(Spacer(1, 0.2*inch))
        
        # Strategic synthesis section
        if 'strategic_synthesis' in internal_data:
            synthesis = internal_data['strategic_synthesis']
            self.story.append(Paragraph(
                synthesis.get('title', 'Strategic Synthesis'),
                self.styles['SubsectionHeader']
            ))
            
            if 'insights' in synthesis:
                for insight in synthesis['insights']:
                    # Create highlighted box for each insight
                    insight_text = Paragraph(
                        f"<b>{insight.get('label', '')}:</b><br/>{insight.get('value', '')}",
                        self.styles['KeyInsight']
                    )
                    self.story.append(insight_text)
                    self.story.append(Spacer(1, 0.05*inch))
            
            if 'description' in synthesis:
                self.story.append(Spacer(1, 0.1*inch))
                self.story.append(Paragraph(
                    synthesis['description'],
                    self.styles['CustomBody']
                ))
            
            self.story.append(Spacer(1, 0.3*inch))
        
        # Cross-indication comparison section
        if 'cross_indication_comparison' in internal_data:
            comparison = internal_data['cross_indication_comparison']
            self.story.append(Paragraph(
                comparison.get('title', 'Cross-Indication Comparison'),
                self.styles['SubsectionHeader']
            ))
            self.story.append(Spacer(1, 0.1*inch))
            
            if 'dimensions' in comparison:
                # Create comparison table
                table_data = [['Dimension', 'Diabetes/Obesity', 'Emerging CNS']]
                for dim in comparison['dimensions']:
                    table_data.append([
                        dim.get('dimension', ''),
                        dim.get('diabetes_obesity', ''),
                        dim.get('emerging_cns', '')
                    ])
                
                table = Table(table_data, colWidths=[2*inch, 2.2*inch, 2.2*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['secondary']),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('TOPPADDING', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 14),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('TEXTCOLOR', (0, 1), (-1, -1), self.COLORS['text']),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, self.COLORS['border']),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.COLORS['lighter']]),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 1), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
                ]))
                self.story.append(table)
            
            if 'description' in comparison:
                self.story.append(Spacer(1, 0.15*inch))
                self.story.append(Paragraph(
                    comparison['description'],
                    self.styles['CustomBody']
                ))
        
        # AUD-specific focus section
        if 'aud_focus' in internal_data:
            aud = internal_data['aud_focus']
            self.story.append(Spacer(1, 0.3*inch))
            self.story.append(Paragraph(
                aud.get('title', 'AUD Focus'),
                self.styles['SubsectionHeader']
            ))
            
            if 'insights' in aud:
                for insight in aud['insights']:
                    insight_text = Paragraph(
                        f"<b>{insight.get('label', '')}:</b><br/>{insight.get('value', '')}",
                        self.styles['KeyInsight']
                    )
                    self.story.append(insight_text)
                    self.story.append(Spacer(1, 0.05*inch))
        
        self.story.append(Spacer(1, 0.3*inch))
    
    def add_iqvia_generic_section(self, data: Dict[str, Any]):
        """Add IQVIA section with generic data rendering"""
        if not data:
            return
            
        self.story.append(PageBreak())
        self.story.append(Paragraph("Market Analysis (IQVIA)", self.styles['SectionHeader']))
        self.story.append(Spacer(1, 0.15*inch))
        
        # Summary banner
        summary = data.get("summary", {})
        if summary and summary.get("researcherQuestion"):
            self._add_summary_banner(summary)
        
        # Key metrics
        if data.get("marketSizeUSD") or data.get("cagrPercent"):
            self.story.append(Paragraph("Key Metrics", self.styles['SubsectionHeader']))
            metrics = []
            if data.get("marketSizeUSD"):
                val = data["marketSizeUSD"]
                val_str = f"${val/1e9:.1f}B" if isinstance(val, (int, float)) and val > 1e6 else str(val)
                metrics.append(("Market Size", val_str))
            if data.get("cagrPercent"):
                val = data["cagrPercent"]
                val_str = f"{val:.1f}%" if isinstance(val, (int, float)) else str(val)
                metrics.append(("CAGR", val_str))
            
            table_data = [["Metric", "Value"]]
            for m in metrics:
                table_data.append([m[0], m[1]])
            
            table = Table(table_data, colWidths=[3*inch, 2.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['primary']),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.COLORS['light']]),
            ]))
            self.story.append(table)
            self.story.append(Spacer(1, 0.2*inch))
        
        # Top articles/reports
        articles = data.get("topArticles", [])
        if articles:
            self.story.append(Paragraph("Market Reports", self.styles['SubsectionHeader']))
            for article in articles[:5]:
                title = article.get("title", "")
                source = article.get("source", "")
                self.story.append(Paragraph(
                    f"• <b>{title}</b> ({source})" if source else f"• <b>{title}</b>",
                    self.styles['CustomBullet']
                ))
            self.story.append(Spacer(1, 0.2*inch))
        
        # Infographics
        infographics = data.get("infographics", [])
        if infographics:
            self.story.append(Paragraph("Data Sources", self.styles['SubsectionHeader']))
            for info in infographics[:3]:
                title = info.get("title", "")
                subtitle = info.get("subtitle", "")
                self.story.append(Paragraph(
                    f"• <b>{title}</b><br/><i>{subtitle}</i>" if subtitle else f"• <b>{title}</b>",
                    self.styles['CustomBullet']
                ))
            self.story.append(Spacer(1, 0.2*inch))
    
    def add_clinical_generic_section(self, data: Dict[str, Any]):
        """Add Clinical section with generic data rendering"""
        if not data:
            return
            
        self.story.append(PageBreak())
        self.story.append(Paragraph("Clinical Evidence", self.styles['SectionHeader']))
        self.story.append(Spacer(1, 0.15*inch))
        
        # Summary banner
        summary = data.get("summary", {})
        if summary and summary.get("researcherQuestion"):
            self._add_summary_banner(summary)
        
        # Trials info
        trials = data.get("trials", {})
        if trials:
            total = trials.get("total_trials", 0)
            self.story.append(Paragraph(f"Total Clinical Trials: <b>{total}</b>", self.styles['CustomBody']))
            self.story.append(Spacer(1, 0.1*inch))
            
            # List some trials
            trial_list = trials.get("trials", [])
            if trial_list:
                self.story.append(Paragraph("Key Trials", self.styles['SubsectionHeader']))
                for trial in trial_list[:5]:
                    nct = trial.get("nct_id", "")
                    title = trial.get("brief_title", trial.get("title", ""))[:100]
                    phase = trial.get("phase", "")
                    status = trial.get("status", "")
                    self.story.append(Paragraph(
                        f"• <b>{nct}</b>: {title}<br/><i>Phase: {phase} | Status: {status}</i>",
                        self.styles['CustomBullet']
                    ))
                self.story.append(Spacer(1, 0.2*inch))
        
        # Analysis
        analysis = data.get("analysis", {})
        if analysis:
            # Phase counts
            phase_counts = analysis.get("phase_counts", {})
            if phase_counts:
                self.story.append(Paragraph("Phase Distribution", self.styles['SubsectionHeader']))
                table_data = [["Phase", "Count"]]
                for phase, count in phase_counts.items():
                    table_data.append([phase, str(count)])
                
                table = Table(table_data, colWidths=[3*inch, 2*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['accent']),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.COLORS['light']]),
                ]))
                self.story.append(table)
                self.story.append(Spacer(1, 0.2*inch))
            
            # Top sponsors
            sponsors = analysis.get("top_sponsors", [])
            if sponsors:
                self.story.append(Paragraph("Top Sponsors", self.styles['SubsectionHeader']))
                for sponsor in sponsors[:5]:
                    name = sponsor.get("sponsor", "Unknown")
                    count = sponsor.get("count", 0)
                    self.story.append(Paragraph(
                        f"• <b>{name}</b>: {count} trials",
                        self.styles['CustomBullet']
                    ))
                self.story.append(Spacer(1, 0.2*inch))
    
    def add_patent_generic_section(self, data: Dict[str, Any]):
        """Add Patent section with generic data rendering"""
        if not data:
            return
            
        self.story.append(PageBreak())
        self.story.append(Paragraph("Patent Landscape", self.styles['SectionHeader']))
        self.story.append(Spacer(1, 0.15*inch))
        
        # Summary banner
        summary = data.get("summary", {})
        if summary and summary.get("researcherQuestion"):
            self._add_summary_banner(summary)
        
        # Patents list
        patents = data.get("patents", [])
        if patents:
            self.story.append(Paragraph(f"Total Patents Found: <b>{len(patents)}</b>", self.styles['CustomBody']))
            self.story.append(Spacer(1, 0.1*inch))
            
            self.story.append(Paragraph("Key Patents", self.styles['SubsectionHeader']))
            for patent in patents[:5]:
                number = patent.get("patent_number", patent.get("id", ""))
                title = patent.get("title", "")[:80]
                assignee = patent.get("assignee", "")
                self.story.append(Paragraph(
                    f"• <b>{number}</b>: {title}<br/><i>Assignee: {assignee}</i>" if assignee else f"• <b>{number}</b>: {title}",
                    self.styles['CustomBullet']
                ))
            self.story.append(Spacer(1, 0.2*inch))
    
    def add_exim_generic_section(self, data: Dict[str, Any]):
        """Add EXIM section with generic data rendering"""
        if not data:
            return
            
        self.story.append(PageBreak())
        self.story.append(Paragraph("Trade & Import/Export Analysis", self.styles['SectionHeader']))
        self.story.append(Spacer(1, 0.15*inch))
        
        # Summary banner
        summary = data.get("summary", {})
        if summary and summary.get("researcherQuestion"):
            self._add_summary_banner(summary)
        
        # Trade data
        trade_data = data.get("trade_data", data.get("analysis", {}))
        if trade_data:
            self.story.append(Paragraph("Trade Overview", self.styles['SubsectionHeader']))
            
            # Render key-value pairs
            for key, value in trade_data.items():
                if isinstance(value, (str, int, float)):
                    self.story.append(Paragraph(
                        f"• <b>{key.replace('_', ' ').title()}</b>: {value}",
                        self.styles['CustomBullet']
                    ))
            self.story.append(Spacer(1, 0.2*inch))
    
    def add_internal_knowledge_generic_section(self, data: Dict[str, Any]):
        """Add Internal Knowledge section with generic data rendering"""
        if not data:
            return
            
        self.story.append(PageBreak())
        self.story.append(Paragraph("Strategic Insights", self.styles['SectionHeader']))
        self.story.append(Spacer(1, 0.15*inch))
        
        # Summary banner
        summary = data.get("summary", {})
        if summary and summary.get("researcherQuestion"):
            self._add_summary_banner(summary)
        
        # Documents
        documents = data.get("documents", [])
        if documents:
            self.story.append(Paragraph("Related Documents", self.styles['SubsectionHeader']))
            for doc in documents[:5]:
                title = doc.get("title", "")
                doc_type = doc.get("type", "")
                self.story.append(Paragraph(
                    f"• <b>{title}</b> ({doc_type})" if doc_type else f"• <b>{title}</b>",
                    self.styles['CustomBullet']
                ))
            self.story.append(Spacer(1, 0.2*inch))
        
        # Insights
        insights = data.get("insights", [])
        if insights:
            self.story.append(Paragraph("Key Insights", self.styles['SubsectionHeader']))
            for insight in insights[:5]:
                if isinstance(insight, dict):
                    self.story.append(Paragraph(
                        f"• {insight.get('text', str(insight))}",
                        self.styles['CustomBullet']
                    ))
                else:
                    self.story.append(Paragraph(f"• {insight}", self.styles['CustomBullet']))
            self.story.append(Spacer(1, 0.2*inch))
    
    def _add_summary_banner(self, summary: Dict[str, Any]):
        """Add a summary banner section"""
        question = summary.get("researcherQuestion", "")
        answer = summary.get("answer", "")
        explainers = summary.get("explainers", [])
        
        # Create banner content
        banner_text = f"<b>{question}</b><br/>"
        banner_text += f"<font color='#{self.COLORS['primary'].hexval()[2:]}' size='14'><b>{answer}</b></font>"
        if explainers:
            banner_text += "<br/>" + " • ".join(explainers)
        
        self.story.append(Paragraph(banner_text, self.styles['KeyInsight']))
        self.story.append(Spacer(1, 0.2*inch))
    
    def add_web_intelligence(self, web_data: Dict[str, Any]):
        """Add Web Intelligence section with news, sentiment, and social analysis"""
        if not web_data:
            return
            
        self.story.append(PageBreak())
        self.story.append(Paragraph("Web Intelligence & Public Sentiment", self.styles['SectionHeader']))
        self.story.append(Spacer(1, 0.15*inch))
        
        # Unwrap nested data structure if present
        data = web_data
        if isinstance(web_data, dict):
            if web_data.get("status") == "success" and web_data.get("data"):
                data = web_data["data"]
            elif "data" in web_data:
                data = web_data["data"]
        
        # Top Signal Summary
        top_signal = data.get("top_signal", {})
        if top_signal and top_signal.get("text"):
            self.story.append(Paragraph("Signal Summary", self.styles['SubsectionHeader']))
            
            signal_text = top_signal.get("text", "")
            score = top_signal.get("score")
            label = top_signal.get("label", "")
            
            # Create a highlighted box for the signal
            signal_content = f"<b>{signal_text}</b>"
            if score is not None:
                signal_content += f"<br/><br/>Signal Score: <b>{score}</b>"
            if label:
                signal_content += f"  |  Alert Level: <b>{label}</b>"
            
            self.story.append(Paragraph(signal_content, self.styles['KeyInsight']))
            self.story.append(Spacer(1, 0.2*inch))
        
        # Sentiment Analysis
        sentiment = data.get("sentiment", data.get("sentiment_summary", {}))
        if sentiment and sentiment.get("total", 0) > 0:
            self.story.append(Paragraph("Sentiment Analysis", self.styles['SubsectionHeader']))
            
            total = sentiment.get("total", 0)
            positive = sentiment.get("positive", 0)
            neutral = sentiment.get("neutral", 0)
            negative = sentiment.get("negative", 0)
            
            # Create sentiment breakdown table
            table_data = [['Sentiment', 'Count', 'Percentage']]
            table_data.append(['Positive', str(positive), f"{(positive/total*100):.0f}%" if total > 0 else "0%"])
            table_data.append(['Neutral', str(neutral), f"{(neutral/total*100):.0f}%" if total > 0 else "0%"])
            table_data.append(['Negative', str(negative), f"{(negative/total*100):.0f}%" if total > 0 else "0%"])
            table_data.append(['Total', str(total), "100%"])
            
            table = Table(table_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['cyan']),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (0, 1), HexColor('#dcfce7')),  # Green for positive
                ('BACKGROUND', (0, 2), (0, 2), HexColor('#fef9c3')),  # Yellow for neutral
                ('BACKGROUND', (0, 3), (0, 3), HexColor('#fee2e2')),  # Red for negative
                ('TEXTCOLOR', (0, 1), (-1, -1), self.COLORS['text']),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            self.story.append(table)
            self.story.append(Spacer(1, 0.2*inch))
        
        # Top Headlines / News
        headlines = data.get("top_headlines", data.get("news_articles", []))
        if headlines:
            self.story.append(Paragraph("Latest News & Headlines", self.styles['SubsectionHeader']))
            
            for idx, article in enumerate(headlines[:6]):  # Limit to 6 headlines
                title = article.get("title", "")
                source = article.get("source", "")
                date = article.get("publishedAt", article.get("date", ""))
                snippet = article.get("snippet", article.get("description", ""))
                
                # Format date if present
                if date:
                    try:
                        from datetime import datetime as dt
                        if isinstance(date, str):
                            parsed_date = dt.fromisoformat(date.replace('Z', '+00:00'))
                            date = parsed_date.strftime("%b %d, %Y")
                    except:
                        pass
                
                # Article entry
                article_text = f"<b>{title}</b>"
                if source or date:
                    article_text += f"<br/><font color='#3b82f6'>{source}</font>"
                    if date:
                        article_text += f" • {date}"
                if snippet:
                    article_text += f"<br/><i>{snippet[:150]}...</i>" if len(snippet) > 150 else f"<br/><i>{snippet}</i>"
                
                self.story.append(Paragraph(article_text, self.styles['CustomBullet']))
                self.story.append(Spacer(1, 0.1*inch))
            
            self.story.append(Spacer(1, 0.1*inch))
        
        # Forum Discussions / Community
        forum_quotes = data.get("forum_quotes", [])
        if forum_quotes:
            self.story.append(Paragraph("Community Discussions", self.styles['SubsectionHeader']))
            
            for idx, forum in enumerate(forum_quotes[:5]):  # Limit to 5 quotes
                quote = forum.get("quote", "")
                site = forum.get("site", "")
                sentiment_label = forum.get("sentiment", "")
                
                sentiment_text = ""
                if sentiment_label == "POS":
                    sentiment_text = " (Positive)"
                elif sentiment_label == "NEG":
                    sentiment_text = " (Negative)"
                elif sentiment_label:
                    sentiment_text = " (Neutral)"
                
                quote_text = f"<i>\"{quote}\"</i>"
                if site:
                    quote_text += f"<br/>— <b>{site}</b>{sentiment_text}"
                
                self.story.append(Paragraph(quote_text, self.styles['CustomBullet']))
                self.story.append(Spacer(1, 0.08*inch))
            
            self.story.append(Spacer(1, 0.1*inch))
        
        # Recommended Actions
        actions = data.get("recommended_actions", [])
        if actions:
            self.story.append(Paragraph("Recommended Actions", self.styles['SubsectionHeader']))
            
            for idx, action in enumerate(actions):
                self.story.append(Paragraph(
                    f"• {action}",
                    self.styles['CustomBullet']
                ))
            
            self.story.append(Spacer(1, 0.1*inch))
        
        # Confidence Level
        confidence = data.get("confidence", "")
        if confidence:
            conf_color = "#10b981" if confidence == "HIGH" else "#f59e0b" if confidence == "MEDIUM" else "#f97316"
            self.story.append(Paragraph(
                f"Analysis Confidence: <b><font color='{conf_color}'>{confidence}</font></b>",
                self.styles['CustomBody']
            ))
        
        self.story.append(Spacer(1, 0.3*inch))
    
    def add_conclusion_and_recommendation(
        self, 
        drug_name: str,
        indication: str,
        patent_data: Dict[str, Any],
        clinical_data: Dict[str, Any],
        iqvia_data: Dict[str, Any],
        exim_data: Dict[str, Any]
    ):
        """
        Add conclusion section with go/no-go recommendation based on all agent findings.
        
        Decision factors:
        - Patent: BLOCKED = No-Go, AT_RISK = Caution, CLEAR = Proceed
        - Clinical: No trials = Caution, Active trials = Positive
        - Market: Small market = Caution, Growing market = Positive
        - EXIM: Import restrictions = No-Go, Low volumes = Caution
        """
        self.story.append(PageBreak())
        self.story.append(Paragraph("Conclusion & Recommendation", self.styles['SectionHeader']))
        self.story.append(Spacer(1, 0.2*inch))
        
        # Analyze findings
        issues = []
        cautions = []
        positives = []
        
        # Patent Analysis
        fto_data = patent_data.get("data", {}) if isinstance(patent_data, dict) else {}
        fto_status = fto_data.get("ftoStatus", "UNKNOWN")
        blocking_patents = fto_data.get("blockingPatents", [])
        
        if fto_status == "BLOCKED":
            issues.append("PATENT BLOCKED: Active blocking patents identified. Immediate legal consultation required.")
        elif fto_status == "AT_RISK":
            cautions.append("Patent Risk: Potential blocking patents identified. FTO opinion recommended.")
        elif fto_status == "CLEAR":
            positives.append("Patent landscape appears clear for the target indication.")
        elif blocking_patents:
            cautions.append(f"{len(blocking_patents)} blocking patent(s) identified - review required.")
        
        # Clinical Analysis
        clinical_analysis = clinical_data.get("data", {}) if isinstance(clinical_data, dict) else {}
        trials = clinical_analysis.get("trials", {})
        total_trials = trials.get("total_trials", 0) if isinstance(trials, dict) else 0
        
        if total_trials == 0:
            cautions.append("Limited clinical evidence: No clinical trials found for this drug-indication pair.")
        elif total_trials < 5:
            cautions.append(f"Early clinical stage: Only {total_trials} clinical trial(s) identified.")
        else:
            positives.append(f"Strong clinical activity: {total_trials} clinical trials identified.")
        
        # Market Analysis (IQVIA)
        iqvia_result = iqvia_data.get("data", {}) if isinstance(iqvia_data, dict) else {}
        market_size = iqvia_result.get("market_size", "")
        
        # EXIM Analysis
        exim_result = exim_data.get("data", {}) if isinstance(exim_data, dict) else {}
        trade_restriction = exim_result.get("restriction_flag", False)
        export_volume = exim_result.get("total_export_volume", 0)
        
        if trade_restriction:
            issues.append("TRADE RESTRICTION: Import/export restrictions identified for this product.")
        elif export_volume and export_volume < 100:
            cautions.append("Low trade volume: Limited export activity may indicate market challenges.")
        
        # Generate recommendation
        if issues:
            recommendation = "NOT RECOMMENDED TO PROCEED"
            recommendation_color = self.COLORS['danger']
            recommendation_text = (
                f"Based on the analysis, proceeding with {drug_name} for {indication} is NOT recommended "
                f"due to critical issues identified. The following blockers must be addressed before considering further development:"
            )
        elif len(cautions) >= 3:
            recommendation = "PROCEED WITH SIGNIFICANT CAUTION"
            recommendation_color = self.COLORS['warning']
            recommendation_text = (
                f"Multiple areas of concern have been identified for {drug_name} in {indication}. "
                f"While not outright blockers, these issues warrant careful consideration and risk mitigation strategies."
            )
        elif cautions:
            recommendation = "PROCEED WITH CAUTION"
            recommendation_color = self.COLORS['warning']
            recommendation_text = (
                f"The overall outlook for {drug_name} in {indication} is cautiously positive. "
                f"However, the following areas require attention during development planning."
            )
        else:
            recommendation = "RECOMMENDED TO PROCEED"
            recommendation_color = self.COLORS['accent']
            recommendation_text = (
                f"The analysis indicates favorable conditions for {drug_name} in {indication}. "
                f"Key indicators suggest this opportunity warrants further investment and development."
            )
        
        # Recommendation Box
        rec_box_data = [[Paragraph(
            f"<b>{recommendation}</b>",
            ParagraphStyle(
                name='RecTitle',
                fontSize=18,
                textColor=colors.white,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
        )]]
        rec_box = Table(rec_box_data, colWidths=[6*inch])
        rec_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), recommendation_color),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 16),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
        ]))
        self.story.append(rec_box)
        self.story.append(Spacer(1, 0.2*inch))
        
        # Recommendation explanation
        self.story.append(Paragraph(recommendation_text, self.styles['CustomBody']))
        self.story.append(Spacer(1, 0.2*inch))
        
        # Critical Issues
        if issues:
            self.story.append(Paragraph("Critical Issues (Blockers)", self.styles['SubsectionHeader']))
            for issue in issues:
                self.story.append(Paragraph(
                    f"• <font color='#dc2626'><b>⚠</b></font> {issue}",
                    self.styles['CustomBullet']
                ))
            self.story.append(Spacer(1, 0.15*inch))
        
        # Cautions
        if cautions:
            self.story.append(Paragraph("Areas of Caution", self.styles['SubsectionHeader']))
            for caution in cautions:
                self.story.append(Paragraph(
                    f"• <font color='#d97706'><b>⚡</b></font> {caution}",
                    self.styles['CustomBullet']
                ))
            self.story.append(Spacer(1, 0.15*inch))
        
        # Positives
        if positives:
            self.story.append(Paragraph("Favorable Indicators", self.styles['SubsectionHeader']))
            for positive in positives:
                self.story.append(Paragraph(
                    f"• <font color='#059669'><b>✓</b></font> {positive}",
                    self.styles['CustomBullet']
                ))
            self.story.append(Spacer(1, 0.15*inch))
        
        # Recommended Next Steps
        self.story.append(Spacer(1, 0.2*inch))
        self.story.append(Paragraph("Recommended Next Steps", self.styles['SubsectionHeader']))
        
        # Generate context-aware next steps based on findings
        next_steps = []
        
        if issues:
            next_steps.append(f"Address critical blockers identified for {drug_name} before proceeding")
            if any("patent" in issue.lower() for issue in issues):
                next_steps.append("Engage patent counsel immediately for FTO opinion and licensing strategy")
        
        if cautions:
            if any("clinical" in caution.lower() for caution in cautions):
                next_steps.append("Conduct expanded clinical literature review and trial landscape analysis")
            if any("market" in caution.lower() or "trade" in caution.lower() for caution in cautions):
                next_steps.append("Perform detailed market sizing with competitive intelligence")
        
        if not next_steps or len(next_steps) < 3:
            # Add default strategic next steps
            default_steps = [
                f"Complete comprehensive due diligence package for {indication} indication",
                "Engage regulatory affairs to map approval pathway and timeline",
                "Develop business case with NPV analysis and risk-adjusted projections"
            ]
            for step in default_steps:
                if step not in next_steps:
                    next_steps.append(step)
                    if len(next_steps) >= 3:
                        break
        
        for step in next_steps[:3]:
            self.story.append(Paragraph(
                f"• {step}",
                self.styles['CustomBullet']
            ))
        
        # Disclaimer
        self.story.append(Spacer(1, 0.3*inch))
        disclaimer_text = (
            "<i>This recommendation is based on automated analysis and should be validated by domain experts. "
            "Consult qualified patent counsel for legal advice and conduct thorough due diligence before making investment decisions.</i>"
        )
        self.story.append(Paragraph(disclaimer_text, ParagraphStyle(
            name='Disclaimer',
            fontSize=9,
            textColor=self.COLORS['text_light'],
            alignment=TA_CENTER,
            spaceBefore=10
        )))
    
    def add_agent_data_section(self, agent_name: str, agent_data: Dict[str, Any]):
        """
        Add a section for any agent data, extracting visualizations and key metrics.
        This is a generic method that works with any agent output format.
        """
        if not agent_data:
            return
            
        self.story.append(PageBreak())
        self.story.append(Paragraph(agent_name, self.styles['SectionHeader']))
        self.story.append(Spacer(1, 0.15*inch))
        
        # Check if this is wrapped in a 'data' key
        data = agent_data.get("data", agent_data) if isinstance(agent_data, dict) else agent_data
        
        # Extract summary if available (could be in data or at top level)
        summary = None
        if isinstance(data, dict):
            summary = data.get("summary")
        if not summary and isinstance(agent_data, dict):
            summary = agent_data.get("summary")
        
        if summary:
            summary_text = str(summary) if not isinstance(summary, dict) else summary.get("executive", str(summary))
            self.story.append(Paragraph(summary_text, self.styles['CustomBody']))
            self.story.append(Spacer(1, 0.2*inch))
        
        # Extract visualizations - check BOTH top level and inside data
        visualizations = []
        if isinstance(agent_data, dict):
            visualizations = agent_data.get("visualizations", [])
        if not visualizations and isinstance(data, dict):
            visualizations = data.get("visualizations", [])
        
        for viz in visualizations:
            if not isinstance(viz, dict):
                continue
                
            viz_type = viz.get("vizType", "").lower()
            title = viz.get("title", "")
            description = viz.get("description", "")
            viz_data = viz.get("data", {})
            
            if title:
                self.story.append(Paragraph(title, self.styles['SubsectionHeader']))
            
            if viz_type in ["card", "metric"]:
                # Metric card - handle both dict and direct value
                if isinstance(viz_data, dict):
                    value = viz_data.get("value", "N/A")
                    unit = viz_data.get("unit", "")
                    if unit:
                        value = f"{value} {unit}"
                else:
                    value = str(viz_data) if viz_data else "N/A"
                self.story.append(Paragraph(
                    f"<b>{value}</b>",
                    ParagraphStyle(name='MetricValue', fontSize=24, textColor=self.COLORS['primary'])
                ))
            
            elif viz_type == "text":
                # Text content - render the description as body text
                if description:
                    self.story.append(Paragraph(description, self.styles['CustomBody']))
                elif isinstance(viz_data, dict) and viz_data.get("content"):
                    self.story.append(Paragraph(viz_data["content"], self.styles['CustomBody']))
                
            elif viz_type == "table":
                # Table visualization
                columns = viz_data.get("columns", [])
                rows = viz_data.get("rows", [])
                
                if columns and rows:
                    # Build table header
                    header = [col.get("label", col.get("key", "")) for col in columns]
                    table_data = [header]
                    
                    # Build table rows (limit to first 10)
                    for row in rows[:10]:
                        row_data = []
                        for col in columns:
                            key = col.get("key", "")
                            val = row.get(key, "")
                            # Truncate long values
                            val_str = str(val)[:50] + "..." if len(str(val)) > 50 else str(val)
                            row_data.append(val_str)
                        table_data.append(row_data)
                    
                    # Calculate column widths
                    num_cols = len(columns)
                    col_width = 6.5 * inch / num_cols
                    
                    table = Table(table_data, colWidths=[col_width] * num_cols)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['primary']),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 9),
                        ('FONTSIZE', (0, 1), (-1, -1), 8),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.COLORS['light']]),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ]))
                    self.story.append(table)
                    
                    if len(rows) > 10:
                        self.story.append(Paragraph(
                            f"<i>Showing 10 of {len(rows)} rows</i>",
                            ParagraphStyle(name='TableNote', fontSize=8, textColor=self.COLORS['text_light'])
                        ))
            
            elif viz_type == "pie":
                # Pie chart - create using matplotlib
                # Handle both formats:
                # Format 1: {"labels": [...], "values": [...]}
                # Format 2: [{"label": "X", "value": Y}, ...]
                if isinstance(viz_data, list):
                    # Format 2: list of {label, value} dicts
                    labels = [item.get("label", "") for item in viz_data if isinstance(item, dict)]
                    values = [item.get("value", 0) for item in viz_data if isinstance(item, dict)]
                elif isinstance(viz_data, dict):
                    # Format 1: separate labels and values arrays
                    labels = viz_data.get("labels", [])
                    values = viz_data.get("values", [])
                else:
                    labels, values = [], []
                
                if labels and values:
                    chart_img = self._create_generic_pie_chart(labels, values, title)
                    if chart_img:
                        self.story.append(chart_img)
            
            elif viz_type == "bar":
                # Bar chart
                items = viz_data if isinstance(viz_data, list) else []
                if items:
                    x_field = viz.get("config", {}).get("xField", "")
                    y_field = viz.get("config", {}).get("yField", "")
                    if x_field and y_field:
                        chart_img = self._create_generic_bar_chart(items, x_field, y_field, title)
                        if chart_img:
                            self.story.append(chart_img)
            
            if description:
                self.story.append(Spacer(1, 0.1*inch))
                self.story.append(Paragraph(description, self.styles['CustomBody']))
            
            self.story.append(Spacer(1, 0.2*inch))
    
    def _create_generic_pie_chart(self, labels: List, values: List, title: str) -> Image:
        """Create a generic pie chart from labels and values."""
        if not labels or not values or len(labels) != len(values):
            return None
        
        try:
            fig, ax = plt.subplots(figsize=(6, 4), facecolor='white')
            
            # Filter out zero values
            filtered = [(l, v) for l, v in zip(labels, values) if v and v > 0]
            if not filtered:
                plt.close()
                return None
            
            labels, values = zip(*filtered)
            
            # Color palette
            colors_list = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#06b6d4']
            
            wedges, texts, autotexts = ax.pie(
                values,
                labels=labels,
                autopct='%1.1f%%',
                colors=colors_list[:len(values)],
                startangle=90,
                textprops={'fontsize': 9},
            )
            
            ax.set_title(title, fontsize=12, fontweight='bold', pad=15)
            plt.tight_layout()
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            img_buffer.seek(0)
            plt.close()
            
            return Image(img_buffer, width=5*inch, height=3.5*inch)
        except Exception as e:
            print(f"Error creating pie chart: {e}")
            plt.close()
            return None
    
    def _create_generic_bar_chart(self, items: List[Dict], x_field: str, y_field: str, title: str) -> Image:
        """Create a generic bar chart from items."""
        if not items:
            return None
        
        try:
            fig, ax = plt.subplots(figsize=(7, 4), facecolor='white')
            
            x_values = [str(item.get(x_field, ""))[:20] for item in items[:10]]
            y_values = [float(item.get(y_field, 0)) for item in items[:10]]
            
            bars = ax.bar(x_values, y_values, color='#3b82f6', edgecolor='#1e40af')
            
            ax.set_xlabel(x_field.replace("_", " ").title(), fontsize=10)
            ax.set_ylabel(y_field.replace("_", " ").title(), fontsize=10)
            ax.set_title(title, fontsize=12, fontweight='bold', pad=15)
            
            plt.xticks(rotation=45, ha='right', fontsize=8)
            plt.tight_layout()
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            img_buffer.seek(0)
            plt.close()
            
            return Image(img_buffer, width=6*inch, height=3.5*inch)
        except Exception as e:
            print(f"Error creating bar chart: {e}")
            plt.close()
            return None
        
    def _create_market_forecast_chart(self, data: List[Dict]) -> Image:
        """Create enhanced market forecast line chart with better styling"""
        if not data:
            return None
            
        # Set style
        plt.style.use('seaborn-v0_8-darkgrid')
        fig, ax = plt.subplots(figsize=(7, 4), facecolor='white')
        
        years = [item['year'] for item in data]
        values = [item['value'] for item in data]
        
        # Create gradient effect with multiple fills
        ax.plot(years, values, marker='o', linewidth=3.5, 
                color='#1e40af', markersize=10, markerfacecolor='#3b82f6',
                markeredgecolor='#1e40af', markeredgewidth=2, 
                label='Market Size', zorder=3)
        
        # Add value labels on points
        for i, (year, value) in enumerate(zip(years, values)):
            ax.text(year, value, f'${value}B', 
                   ha='center', va='bottom', fontsize=9, 
                   fontweight='bold', color='#1e40af')
        
        # Fill area with gradient
        ax.fill_between(years, values, alpha=0.3, color='#3b82f6', zorder=2)
        ax.fill_between(years, values, alpha=0.15, color='#60a5fa', zorder=1)
        
        # Styling
        ax.set_xlabel('Year', fontsize=11, fontweight='bold', color='#374151')
        ax.set_ylabel('Market Size (USD Billions)', fontsize=11, fontweight='bold', color='#374151')
        ax.set_title('GLP-1 Market Forecast & Growth Trajectory', 
                    fontsize=13, fontweight='bold', pad=20, color='#1f2937')
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
        ax.set_facecolor('#f9fafb')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#d1d5db')
        ax.spines['bottom'].set_color('#d1d5db')
        ax.legend(loc='upper left', framealpha=0.9, fontsize=10)
        
        plt.tight_layout()
        
        # Save to buffer
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=200, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        img_buffer.seek(0)
        plt.close()
        
        # Create ReportLab Image
        img = Image(img_buffer, width=6*inch, height=3.5*inch)
        return img
        
    def _create_phase_distribution_chart(self, data: List[Dict]) -> Image:
        """Create enhanced phase distribution pie chart with better visuals"""
        if not data:
            return None
            
        fig, ax = plt.subplots(figsize=(7, 5), facecolor='white')
        
        phases = [item['phase'] for item in data]
        counts = [int(item['count']) for item in data]
        
        # Enhanced color palette with gradients
        colors_map = {
            'Phase I': '#3b82f6',    # Blue
            'Phase II': '#10b981',   # Green
            'Phase III': '#f59e0b',  # Amber
            'Phase IV': '#8b5cf6'    # Purple
        }
        colors_list = [colors_map.get(phase, '#6b7280') for phase in phases]
        
        # Create explode effect for emphasis
        explode = [0.05] * len(phases)
        
        # Create pie chart with enhanced styling
        wedges, texts, autotexts = ax.pie(
            counts, 
            labels=phases, 
            autopct='%1.1f%%',
            colors=colors_list,
            startangle=90,
            textprops={'fontsize': 11, 'fontweight': 'bold', 'color': '#1f2937'},
            explode=explode,
            shadow=True,
            wedgeprops={'edgecolor': 'white', 'linewidth': 2, 'antialiased': True}
        )
        
        # Style percentage labels
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(10)
            autotext.set_fontweight('bold')
        
        # Add legend with counts
        legend_labels = [f'{phase}: {count} trials' for phase, count in zip(phases, counts)]
        ax.legend(legend_labels, loc='center left', bbox_to_anchor=(1, 0, 0.5, 1),
                 framealpha=0.9, fontsize=9)
        
        ax.set_title('Clinical Trial Phase Distribution', 
                    fontsize=14, fontweight='bold', pad=20, color='#1f2937')
        
        plt.tight_layout()
        
        # Save to buffer
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=200, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        img_buffer.seek(0)
        plt.close()
        
        # Create ReportLab Image
        img = Image(img_buffer, width=6*inch, height=4*inch)
        return img
        
    def build(self):
        """Build the PDF document"""
        self.doc.build(self.story)


# Core PDF generation function (not decorated, always callable)
def _generate_pdf_core(
    drug_name: str,
    indication: str,
    iqvia_data: dict,
    exim_data: dict,
    patent_data: dict,
    clinical_data: dict,
    internal_knowledge_data: dict,
    report_data: dict,
    web_intelligence_data: dict = None,
    visualizations: dict = None,
) -> dict:
    """
    Core PDF generation logic.
    This function is always callable regardless of CrewAI installation.
    
    Enhanced to work with actual agent output format including visualizations.
    
    Args:
        drug_name: Name of the drug
        indication: Indication type ("general" or specific indication)
        iqvia_data: Market data from IQVIA agent
        exim_data: Trade data from EXIM agent
        patent_data: Patent landscape from Patent agent
        clinical_data: Clinical trials data from Clinical agent
        internal_knowledge_data: Strategic insights from Internal Knowledge agent
        report_data: Report metadata
        web_intelligence_data: Web intelligence data (optional)
        visualizations: Dict of visualization arrays per agent (optional)
    
    Returns:
        Dictionary with PDF generation status and file path
    """
    # Check if required dependencies are available
    deps_ok, error_msg = check_dependencies()
    if not deps_ok:
        return {
            "status": "error",
            "message": "Missing required dependencies for PDF generation",
            "error": error_msg
        }
    
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "generated_reports")
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_drug_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in drug_name)
        safe_indication = "".join(c if c.isalnum() or c in "._- " else "_" for c in indication)
        filename = os.path.join(
            output_dir, 
            f"{safe_drug_name.replace(' ', '_')}_{safe_indication}_{timestamp}.pdf"
        )
        
        # Create PDF generator
        pdf = PDFReportGenerator(filename)
        
        # Add cover page
        indication_display = indication.title() if indication != "general" else "Comprehensive Drug Analysis"
        pdf.add_cover_page(drug_name, indication_display)
        
        # Add executive summary from report_data if available
        if report_data:
            pdf.add_executive_summary(report_data)
        
        # Helper function to unwrap nested agent data structure
        # Agents return: {status: "success", data: {...actual...}}
        # Orchestrator stores: {timestamp, query, data: agent_return}
        # So full path is: agent_data.data.data for actual content
        def unwrap_agent_data(agent_data):
            """Unwrap potentially nested agent data to get actual content."""
            if not agent_data or not isinstance(agent_data, dict):
                print(f"[PDF] unwrap_agent_data: empty or non-dict input")
                return {}
            
            print(f"[PDF] unwrap_agent_data input keys: {list(agent_data.keys())}")
            
            # Check for direct status/data pattern first
            if agent_data.get("status") == "success" and "data" in agent_data:
                inner = agent_data.get("data", {})
                print(f"[PDF] unwrap_agent_data: found status/data pattern, inner keys: {list(inner.keys()) if isinstance(inner, dict) else 'not dict'}")
                return inner if isinstance(inner, dict) else {}
            
            # Check for orchestrator wrapper: {timestamp, query, data: agent_return}
            inner = agent_data.get("data", agent_data)
            print(f"[PDF] unwrap_agent_data: inner type={type(inner).__name__}")
            
            # If inner has status/data, unwrap again
            if isinstance(inner, dict):
                print(f"[PDF] unwrap_agent_data: inner keys: {list(inner.keys())}")
                if inner.get("status") == "success" and "data" in inner:
                    result = inner.get("data", {})
                    print(f"[PDF] unwrap_agent_data: final result keys: {list(result.keys()) if isinstance(result, dict) else 'not dict'}")
                    return result if isinstance(result, dict) else {}
                return inner
            
            return {}
        
        # ===== AGENT SECTIONS WITH VISUALIZATION SUPPORT =====
        
        # Helper to convert new agent format to PDF-compatible format
        def adapt_clinical_data(data):
            """Convert new clinical agent format to PDF-compatible format."""
            if not data:
                return data
            
            # If already has old format keys, return as-is
            if "phase_distribution" in data or "sponsor_profile" in data:
                return data
            
            # Convert new format: analysis.phase_counts -> phase_distribution
            analysis = data.get("analysis", {})
            trials_data = data.get("trials", {})
            
            result = dict(data)  # Copy original
            
            # Build phase_distribution from analysis.phase_counts
            if analysis and analysis.get("phase_counts"):
                phase_data = []
                for phase, count in analysis["phase_counts"].items():
                    color = "blue" if "1" in phase or "I" in phase else "green" if "2" in phase or "II" in phase else "amber"
                    phase_data.append({"phase": phase, "count": count, "color": color})
                result["phase_distribution"] = {
                    "title": "Trial Phase Distribution",
                    "data": phase_data,
                    "description": f"Distribution of {trials_data.get('total_trials', 0)} clinical trials by phase."
                }
            
            # Build sponsor_profile from analysis.top_sponsors
            if analysis and analysis.get("top_sponsors"):
                sponsor_data = []
                for sponsor in analysis["top_sponsors"][:5]:
                    sponsor_data.append({
                        "sponsor": sponsor.get("sponsor", "Unknown"),
                        "trial_count": sponsor.get("count", 0),
                        "focus": sponsor.get("focus", "General research")
                    })
                result["sponsor_profile"] = {
                    "title": "Top Trial Sponsors",
                    "data": sponsor_data,
                    "description": "Leading organizations conducting clinical trials."
                }
            
            # Build landscape_overview
            drug_name = data.get("input", {}).get("drug_name", "")
            condition = data.get("input", {}).get("condition", "")
            total = trials_data.get("total_trials", 0)
            result["landscape_overview"] = {
                "title": f"Clinical Trial Landscape: {drug_name or condition}",
                "description": f"Found {total} clinical trials for this drug-condition pair."
            }
            
            return result
        
        def adapt_iqvia_data(data):
            """Ensure IQVIA data has expected structure."""
            if not data:
                return data
            
            result = dict(data)
            
            # Build market_forecast if we have infographics or top_articles
            if "market_forecast" not in result:
                if result.get("infographics") or result.get("topArticles"):
                    result["market_forecast"] = {
                        "title": "Market Intelligence",
                        "description": f"Market analysis based on {len(result.get('infographics', []))} data sources and {len(result.get('topArticles', []))} market reports."
                    }
            
            return result
        
        def adapt_exim_data(data):
            """Convert EXIM agent data to PDF-compatible format."""
            if not data:
                return data
            if "export_summary" in data or "import_summary" in data or "trade_volume" in data:
                return data
            
            result = dict(data)
            analysis = data.get("analysis", {})
            
            # Create summaries from analysis if available
            if analysis:
                if analysis.get("total_exports"):
                    result["export_summary"] = {
                        "total_value": str(analysis.get("total_exports", 0)),
                        "top_destination": analysis.get("top_export_destination", "")
                    }
                if analysis.get("total_imports"):
                    result["import_summary"] = {
                        "total_value": str(analysis.get("total_imports", 0)),
                        "top_source": analysis.get("top_import_source", "")
                    }
            
            return result
        
        def adapt_patent_data(data):
            """Convert patent agent data to PDF-compatible format."""
            if not data:
                return data
            if "landscape_overview" in data:
                return data
            
            result = dict(data)
            
            # Build landscape_overview from available data
            drug = data.get("input", {}).get("drug", "")
            total_patents = len(data.get("patents", []))
            result["landscape_overview"] = {
                "title": f"Patent Landscape: {drug}" if drug else "Patent Landscape Analysis",
                "description": f"Analysis of {total_patents} patents in this therapeutic area."
            }
            
            return result
        
        def adapt_internal_knowledge_data(data):
            """Convert internal knowledge agent data to PDF-compatible format."""
            if not data:
                return data
            if "strategic_synthesis" in data:
                return data
            
            result = dict(data)
            
            # Build strategic_synthesis from summary or other fields
            summary = data.get("summary", {})
            if summary:
                insights = []
                if summary.get("answer"):
                    insights.append({"label": "Strategic Assessment", "value": summary.get("answer")})
                for explainer in summary.get("explainers", []):
                    insights.append({"label": "Key Insight", "value": explainer})
                
                result["strategic_synthesis"] = {
                    "title": "Strategic Synthesis",
                    "insights": insights,
                    "description": summary.get("researcherQuestion", "")
                }
            
            return result
        
        # Market Analysis (IQVIA)
        if iqvia_data:
            iqvia_inner = adapt_iqvia_data(unwrap_agent_data(iqvia_data))
            print(f"[PDF] IQVIA data keys: {list(iqvia_inner.keys()) if iqvia_inner else 'empty'}")
            # Try old format first, then use generic visualization-based approach
            if "market_forecast" in iqvia_inner or "competitive_share" in iqvia_inner:
                pdf.add_market_analysis(iqvia_inner, indication)
            elif iqvia_inner:
                pdf.add_iqvia_generic_section(iqvia_inner)
        
        # Clinical Analysis
        if clinical_data:
            clinical_inner = adapt_clinical_data(unwrap_agent_data(clinical_data))
            print(f"[PDF] Clinical data keys: {list(clinical_inner.keys()) if clinical_inner else 'empty'}")
            if "phase_distribution" in clinical_inner or "sponsor_profile" in clinical_inner:
                pdf.add_clinical_analysis(clinical_inner, indication)
            elif clinical_inner:
                pdf.add_clinical_generic_section(clinical_inner)
        
        # Patent Analysis
        if patent_data:
            patent_inner = adapt_patent_data(unwrap_agent_data(patent_data))
            print(f"[PDF] Patent data keys: {list(patent_inner.keys()) if patent_inner else 'empty'}")
            if "landscape_overview" in patent_inner:
                pdf.add_patent_analysis(patent_inner, indication)
            elif patent_inner:
                pdf.add_patent_generic_section(patent_inner)
        
        # EXIM Analysis
        if exim_data:
            exim_inner = adapt_exim_data(unwrap_agent_data(exim_data))
            print(f"[PDF] EXIM data keys: {list(exim_inner.keys()) if exim_inner else 'empty'}")
            if "export_summary" in exim_inner or "import_summary" in exim_inner or "trade_volume" in exim_inner:
                pdf.add_exim_analysis(exim_inner)
            elif exim_inner:
                pdf.add_exim_generic_section(exim_inner)
        
        # Internal Knowledge
        if internal_knowledge_data:
            internal_inner = adapt_internal_knowledge_data(unwrap_agent_data(internal_knowledge_data))
            print(f"[PDF] Internal Knowledge data keys: {list(internal_inner.keys()) if internal_inner else 'empty'}")
            if "strategic_synthesis" in internal_inner:
                pdf.add_internal_knowledge(internal_inner)
            elif internal_inner:
                pdf.add_internal_knowledge_generic_section(internal_inner)
        
        # Web Intelligence - use dedicated method for proper formatting
        if web_intelligence_data:
            print(f"[PDF] Web Intelligence data: processing...")
            pdf.add_web_intelligence(web_intelligence_data)
        
        # ===== CONCLUSION SECTION =====
        pdf.add_conclusion_and_recommendation(
            drug_name=drug_name,
            indication=indication,
            patent_data=patent_data or {},
            clinical_data=clinical_data or {},
            iqvia_data=iqvia_data or {},
            exim_data=exim_data or {}
        )
        
        # Build the PDF
        pdf.build()
        
        return {
            "status": "success",
            "message": f"PDF report generated successfully",
            "file_path": filename,
            "file_name": os.path.basename(filename),
            "drug_name": drug_name,
            "indication": indication,
            "timestamp": timestamp
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"Failed to generate PDF: {str(e)}",
            "error": str(e)
        }


# CrewAI tool wrapper (only used when CrewAI calls it)
@tool("generate_pdf_report")
def generate_pdf_report(
    drug_name: str,
    indication: str,
    iqvia_data: dict,
    exim_data: dict,
    patent_data: dict,
    clinical_data: dict,
    internal_knowledge_data: dict,
    report_data: dict
) -> dict:
    """
    Generate a comprehensive PDF report with all agent data.
    
    This is the CrewAI tool wrapper. For standalone usage, use create_pdf_report() instead.
    
    Args:
        drug_name: Name of the drug
        indication: Indication type ("general" or "aud")
        iqvia_data: Market data from IQVIA agent
        exim_data: Trade data from EXIM agent
        patent_data: Patent landscape from Patent agent
        clinical_data: Clinical trials data from Clinical agent
        internal_knowledge_data: Strategic insights from Internal Knowledge agent
        report_data: Report metadata
    
    Returns:
        Dictionary with PDF generation status and file path
    """
    # Check if required dependencies are available
    deps_ok, error_msg = check_dependencies()
    if not deps_ok:
        return {
            "status": "error",
            "message": "Missing required dependencies for PDF generation",
            "error": error_msg
        }
    
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "generated_reports")
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(
            output_dir, 
            f"{drug_name.replace(' ', '_')}_{indication}_{timestamp}.pdf"
        )
        
        # Create PDF generator
        pdf = PDFReportGenerator(filename)
        
        # Add cover page
        indication_display = "Alcohol Use Disorder (AUD) Analysis" if indication == "aud" else "Comprehensive Drug Repurposing Analysis"
        pdf.add_cover_page(drug_name, indication_display)
        
        # Add executive summary
        pdf.add_executive_summary(report_data)
        
        # Add market analysis
        pdf.add_market_analysis(iqvia_data, indication)
        
        # Add clinical analysis
        pdf.add_clinical_analysis(clinical_data, indication)
        
        # Add patent analysis
        pdf.add_patent_analysis(patent_data, indication)
        
        # Add EXIM analysis (only for first prompt)
        if indication == "general" and exim_data:
            pdf.add_exim_analysis(exim_data)
        
        # Add internal knowledge
        pdf.add_internal_knowledge(internal_knowledge_data)
        
        # Build the PDF
        pdf.build()
        
        return {
            "status": "success",
            "message": f"PDF report generated successfully",
            "file_path": filename,
            "file_name": os.path.basename(filename),
            "drug_name": drug_name,
            "indication": indication,
            "timestamp": timestamp
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to generate PDF: {str(e)}",
            "error": str(e)
        }


# Standalone function for direct usage (without CrewAI tool wrapper)
def create_pdf_report(**kwargs):
    """
    Standalone function to generate PDF report without CrewAI dependency.
    This always works regardless of CrewAI installation.
    
    Usage:
        result = create_pdf_report(
            drug_name="semaglutide",
            indication="general",
            iqvia_data={...},
            exim_data={...},
            patent_data={...},
            clinical_data={...},
            internal_knowledge_data={...},
            report_data={...}
        )
    
    Returns:
        Dictionary with PDF generation status and file path
    """
    # Call the core function directly (bypasses the Tool wrapper)
    return _generate_pdf_core(**kwargs)


def create_comparison_pdf_report(comparisons: list) -> dict:
    """
    Generate a comparison PDF report for multiple drug analyses.
    
    Args:
        comparisons: List of dictionaries containing:
            - prompt_id: str
            - drug_name: str
            - indication: str
            - agents: dict with agent data
    
    Returns:
        Dictionary with PDF generation status and file path
    """
    deps_ok, error_msg = check_dependencies()
    if not deps_ok:
        return {
            "status": "error",
            "message": "Missing required dependencies for PDF generation",
            "error": error_msg
        }
    
    try:
        # Create output directory
        output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "generated_reports")
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        drug_names = [c["drug_name"] for c in comparisons]
        filename = os.path.join(
            output_dir,
            f"comparison_{'_vs_'.join(d[:10] for d in drug_names)}_{timestamp}.pdf"
        )
        
        # Create PDF generator
        pdf = PDFReportGenerator(filename)
        
        # Add comparison cover page
        pdf.story.append(Spacer(1, 1.5*inch))
        
        title = Paragraph(
            "<b>PHARMACEUTICAL COMPARISON REPORT</b>",
            ParagraphStyle(
                name='ComparisonTitle',
                fontSize=28,
                textColor=pdf.COLORS['primary'],
                alignment=TA_CENTER,
                fontName='Helvetica-Bold',
                leading=34,
                spaceAfter=20
            )
        )
        pdf.story.append(title)
        
        # List drugs being compared
        drug_list = "<br/>".join([f"• <b>{c['drug_name']}</b> ({c['indication']})" for c in comparisons])
        subtitle = Paragraph(
            f"<b>Comparing:</b><br/>{drug_list}",
            ParagraphStyle(
                name='ComparisonSubtitle',
                fontSize=14,
                textColor=pdf.COLORS['text'],
                alignment=TA_CENTER,
                leading=22,
                spaceAfter=40
            )
        )
        pdf.story.append(subtitle)
        
        # Date
        date_text = Paragraph(
            f"<i>Generated: {datetime.now().strftime('%B %d, %Y')}</i>",
            ParagraphStyle(
                name='ComparisonDate',
                fontSize=11,
                textColor=pdf.COLORS['text_light'],
                alignment=TA_CENTER
            )
        )
        pdf.story.append(date_text)
        pdf.story.append(PageBreak())
        
        # ===== SUMMARY COMPARISON TABLE =====
        pdf.story.append(Paragraph("Executive Comparison", pdf.styles['SectionHeader']))
        
        # Build comparison table
        headers = ["Metric"] + [c["drug_name"][:15] for c in comparisons]
        rows = [headers]
        
        # Extract key metrics for each comparison
        for metric_name, extractor in [
            ("FTO Status", lambda agents: agents.get("PATENT_AGENT", {}).get("data", {}).get("visualizations", [{}])[0].get("data", {}).get("value", "N/A") if agents.get("PATENT_AGENT", {}).get("data", {}).get("visualizations") else "N/A"),
            ("Clinical Trials", lambda agents: len(agents.get("CLINICAL_AGENT", {}).get("data", {}).get("visualizations", [{}])[0].get("data", {}).get("rows", [])) if agents.get("CLINICAL_AGENT", {}).get("data", {}).get("visualizations") else "N/A"),
            ("Market Size", lambda agents: agents.get("IQVIA_AGENT", {}).get("data", {}).get("marketSizeUSD", "N/A")),
            ("Trade Partners", lambda agents: agents.get("EXIM_AGENT", {}).get("data", {}).get("summary", {}).get("trading_partners_count", "N/A")),
        ]:
            row = [metric_name]
            for comp in comparisons:
                try:
                    value = extractor(comp["agents"])
                    row.append(str(value) if value else "N/A")
                except:
                    row.append("N/A")
            rows.append(row)
        
        # Create table
        col_widths = [1.5*inch] + [1.2*inch] * len(comparisons)
        table = Table(rows, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), pdf.COLORS['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (0, -1), pdf.COLORS['lighter']),
            ('GRID', (0, 0), (-1, -1), 1, pdf.COLORS['border']),
            ('ROWBACKGROUNDS', (1, 1), (-1, -1), [colors.white, pdf.COLORS['lighter']]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        pdf.story.append(table)
        pdf.story.append(Spacer(1, 30))
        
        # ===== INDIVIDUAL DRUG SECTIONS =====
        for idx, comp in enumerate(comparisons):
            pdf.story.append(PageBreak())
            
            # Drug section header
            pdf.story.append(Paragraph(
                f"Analysis: {comp['drug_name']} ({comp['indication']})",
                pdf.styles['SectionHeader']
            ))
            
            agents = comp["agents"]
            
            # Patent status
            if agents.get("PATENT_AGENT", {}).get("data"):
                patent_data = agents["PATENT_AGENT"]["data"]
                pdf.add_agent_data_section(
                    f"Patent Analysis - {comp['drug_name']}",
                    patent_data
                )
            
            # Clinical summary
            if agents.get("CLINICAL_AGENT", {}).get("data"):
                clinical_data = agents["CLINICAL_AGENT"]["data"]
                pdf.add_agent_data_section(
                    f"Clinical Evidence - {comp['drug_name']}",
                    clinical_data
                )
            
            # Market summary
            if agents.get("IQVIA_AGENT", {}).get("data"):
                iqvia_data = agents["IQVIA_AGENT"]["data"]
                pdf.add_agent_data_section(
                    f"Market Analysis - {comp['drug_name']}",
                    iqvia_data
                )
        
        # ===== CONCLUSION SECTION =====
        pdf.story.append(PageBreak())
        pdf.story.append(Paragraph("Conclusion & Recommendations", pdf.styles['SectionHeader']))
        
        # Generate comparison conclusion
        conclusion_text = f"""
        <b>Comparative Assessment Summary</b><br/><br/>
        
        After analyzing {len(comparisons)} drug candidates, the following recommendations are provided:
        """
        
        pdf.story.append(Paragraph(conclusion_text, pdf.styles['CustomBody']))
        pdf.story.append(Spacer(1, 15))
        
        # Analyze each drug and collect scores for ranking
        drug_scores = []
        
        for comp in comparisons:
            agents = comp["agents"]
            fto_status = "UNKNOWN"
            clinical_trials = 0
            decisive_factors = []
            score = 50  # Base score
            
            # Extract FTO status
            patent_data = agents.get("PATENT_AGENT", {}).get("data", {})
            if patent_data.get("visualizations"):
                for viz in patent_data["visualizations"]:
                    if viz.get("id") == "fto_status" or viz.get("title", "").lower().find("fto") >= 0:
                        fto_status = viz.get("data", {}).get("value", "UNKNOWN")
                        break
            
            # Extract clinical trial count
            clinical_data = agents.get("CLINICAL_AGENT", {}).get("data", {})
            if clinical_data:
                trials = clinical_data.get("trials", {})
                clinical_trials = trials.get("total_trials", 0) if isinstance(trials, dict) else 0
            
            # Scoring and decisive factors
            if fto_status in ["BLOCKED", "HIGH_RISK"]:
                rec = "NOT RECOMMENDED - Patent barriers identified"
                rec_color = pdf.COLORS['danger']
                score -= 40
                decisive_factors.append("Patent BLOCKED")
            elif fto_status in ["AT_RISK", "MODERATE"]:
                rec = "PROCEED WITH CAUTION - Some IP concerns"
                rec_color = pdf.COLORS['warning']
                score -= 15
                decisive_factors.append("Patent AT_RISK")
            else:
                rec = "RECOMMENDED TO PROCEED - Favorable landscape"
                rec_color = pdf.COLORS['accent']
                score += 20
                decisive_factors.append("Patent CLEAR")
            
            if clinical_trials > 10:
                score += 20
                decisive_factors.append(f"Strong clinical evidence ({clinical_trials} trials)")
            elif clinical_trials > 0:
                score += 10
                decisive_factors.append(f"Clinical evidence exists ({clinical_trials} trials)")
            else:
                score -= 10
                decisive_factors.append("Limited clinical data")
            
            drug_scores.append({
                "name": comp['drug_name'],
                "score": score,
                "rec": rec,
                "rec_color": rec_color,
                "decisive_factors": decisive_factors
            })
        
        # Sort by score to identify top candidate
        drug_scores.sort(key=lambda x: x["score"], reverse=True)
        top_candidate = drug_scores[0]["name"] if drug_scores else "Unknown"
        
        # Add decisive factors summary
        pdf.story.append(Paragraph("<b>Decisive Factors:</b>", pdf.styles['SubsectionHeader']))
        pdf.story.append(Spacer(1, 8))
        
        for drug in drug_scores:
            factors_text = f"<b>{drug['name']}:</b> {'; '.join(drug['decisive_factors'])}"
            pdf.story.append(Paragraph(f"• {factors_text}", pdf.styles['CustomBullet']))
        
        pdf.story.append(Spacer(1, 15))
        
        # Add top candidate recommendation
        if len(drug_scores) > 1:
            top_rec = Paragraph(
                f"<b>Top Candidate:</b> Based on comparative analysis, <b>{top_candidate}</b> shows the most favorable profile.",
                ParagraphStyle(
                    name='TopRec',
                    fontSize=12,
                    textColor=pdf.COLORS['accent'],
                    backColor=pdf.COLORS['lighter'],
                    borderWidth=1,
                    borderColor=pdf.COLORS['accent'],
                    borderPadding=10,
                    spaceAfter=15
                )
            )
            pdf.story.append(top_rec)
        
        pdf.story.append(Spacer(1, 10))
        pdf.story.append(Paragraph("<b>Individual Assessments:</b>", pdf.styles['SubsectionHeader']))
        pdf.story.append(Spacer(1, 8))
        
        # Per-drug recommendation
        for drug in drug_scores:
            rec_para = Paragraph(
                f"<b>{drug['name']}:</b> {drug['rec']}",
                ParagraphStyle(
                    name='DrugRec',
                    fontSize=11,
                    textColor=drug['rec_color'],
                    leftIndent=20,
                    spaceAfter=10
                )
            )
            pdf.story.append(rec_para)
        
        # Next steps
        pdf.story.append(Spacer(1, 20))
        pdf.story.append(Paragraph("<b>Recommended Next Steps:</b>", pdf.styles['SubsectionHeader']))
        
        next_steps = [
            "Conduct detailed patent freedom-to-operate analysis for top candidates",
            "Engage with regulatory affairs to assess approval pathways",
            "Perform detailed market sizing and competitive landscape analysis"
        ]
        
        for step in next_steps:
            pdf.story.append(Paragraph(f"• {step}", pdf.styles['CustomBullet']))
        
        # Build PDF
        pdf.build()
        
        return {
            "status": "success",
            "message": "Comparison PDF generated successfully",
            "file_path": filename,
            "file_name": os.path.basename(filename),
            "drugs_compared": [c["drug_name"] for c in comparisons],
            "timestamp": timestamp
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"Failed to generate comparison PDF: {str(e)}",
            "error": str(e)
        }
