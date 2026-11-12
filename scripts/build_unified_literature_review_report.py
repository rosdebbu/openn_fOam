"""
Builds the unified joint UROP Literature Review & Scope Definition Report PDF
for BOTH Debjit Das (RA2411056010276) and Anshumaan Das (RA2411056010283).

Milestone: Literature Review (Review of existing literature and defining scope)
Project: UR2627GEN317 - OpenZess Web CFD Platform
SRM Institute of Science and Technology
"""

import os
import sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#475569"))
        
        # Header (Pages 2+)
        if self._pageNumber > 1:
            self.drawString(36, 810, "SRM Institute of Science and Technology | UROP Project UR2627GEN317")
            self.drawRightString(559, 810, "Literature Review & Scope Definition Report")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(36, 803, 559, 803)
            
        # Footer (All pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(36, 38, 559, 38)
        
        footer_text = "OpenZess: AI-Augmented Web-Native CFD Platform • Project UR2627GEN317 • Debjit Das & Anshumaan Das"
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawString(36, 26, footer_text)
        self.drawRightString(559, 26, page_str)
        self.restoreState()

def create_story():
    styles = getSampleStyleSheet()

    title_main = ParagraphStyle(
        'TitleMain',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#0F172A"),
        alignment=1,
        spaceAfter=2
    )

    title_sub = ParagraphStyle(
        'TitleSub',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12.5,
        textColor=colors.HexColor("#1E3A8A"),
        alignment=1,
        spaceAfter=4
    )

    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#334155"),
        alignment=1
    )

    badge_style = ParagraphStyle(
        'BadgeStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#065F46"),
        alignment=1
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#0D233A"),
        spaceBefore=7,
        spaceAfter=2,
        keepWithNext=False
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#1E293B"),
        alignment=4, # Justify
        spaceAfter=3
    )

    tbl_head_style = ParagraphStyle(
        'TblHead',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.2,
        leading=9.2,
        textColor=colors.HexColor("#0F172A")
    )

    tbl_cell_style = ParagraphStyle(
        'TblCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#1E293B")
    )

    story = []

    # Header Banner
    story.append(Paragraph("SRM INSTITUTE OF SCIENCE AND TECHNOLOGY", title_main))
    story.append(Paragraph("UNDERGRADUATE RESEARCH OPPORTUNITY PROGRAM (UROP) • MILESTONE PROGRESS REPORT", title_sub))
    story.append(Spacer(1, 2))

    # Metadata Block
    meta_text = (
        "<b>Project Title:</b> OpenZess Studio: AI-Augmented High-Performance Web CFD Platform<br/>"
        "<b>Project Code:</b> UR2627GEN317 &nbsp;|&nbsp; <b>Milestone:</b> Literature Review &amp; Scope Definition (Review of existing literature and defining scope)<br/>"
        "<b>Student Investigators:</b> <b>Debjit Das (RA2411056010276)</b> [Lead Submitter] &amp; <b>Anshumaan Das (RA2411056010283)</b> [Co-Investigator]<br/>"
        "<b>Department:</b> Department of Computing Technologies, School of Computing &nbsp;|&nbsp; <b>Hours Logged:</b> 12.00 Hours"
    )
    story.append(Paragraph(meta_text, meta_style))
    story.append(Spacer(1, 3))

    # Status Badge
    badge_table = Table([[Paragraph("STATUS: LITERATURE REVIEW &amp; SCOPE DEFINITION MILESTONE VERIFIED — JOINT RESEARCH PROGRESS", badge_style)]], colWidths=[523])
    badge_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#ECFDF5")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#A7F3D0")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    story.append(badge_table)
    story.append(Spacer(1, 4))

    # SECTION 1: UNIFIED WORK DESCRIPTION FOR PORTAL
    story.append(Paragraph("1. Work Completed During This Logged Period (Portal Progress Description)", h2_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#CBD5E1"), spaceBefore=1, spaceAfter=4))

    desc_p1 = (
        "Conducted a comprehensive multi-disciplinary literature review and established the formal technical scope and architecture "
        "for Project <b>UR2627GEN317</b> (OpenZess: AI-Augmented Web-Native CFD Platform). The collaborative research synthesized classical numerical "
        "methods, deep learning surrogate modeling, bare-metal systems compute, and web-native 3D telemetry to design an accessible, zero-install "
        "fluid dynamics simulation platform."
    )
    story.append(Paragraph(desc_p1, body_style))

    work_items = [
        "<b>Pillar 1: Numerical Discretization &amp; Navier-Stokes Formulations:</b> "
        "Analyzed Chorin's projection (fractional-step) method for incompressible Navier-Stokes equations, decoupling momentum advection-diffusion from the "
        "pressure Poisson constraint (&nabla;&sup2;p = [&rho;/&Delta;t]&nabla;&middot;u*). Reviewed collocated finite volume methods (Jasak, 1996; Weller et al., 1998) "
        "and Rhie-Chow momentum interpolation to eliminate checkerboard pressure oscillations. Integrated Boussinesq thermal buoyancy body forces (Tritton, 1988) "
        "to accurately model natural and mixed convection without fully compressible equation costs.",

        "<b>Pillar 2: Deep Learning Surrogates &amp; Physics-Informed Neural Networks (PINNs):</b> "
        "Evaluated physics-informed loss formulation (Raissi et al., 2019) where continuous PDE residuals constrain neural networks without requiring extensive "
        "labeled training datasets. Surveyed Fourier Neural Operators (Li et al., 2020) for mesh-invariant operator learning, establishing the framework for "
        "instantaneous (&lt;50 ms) aerodynamic drag, pressure distribution, and wake recirculation inference alongside classical iterative solvers.",

        "<b>Pillar 3: High-Performance Compute &amp; In-Browser WebAssembly (WASM):</b> "
        "Researched multi-threaded Rust compute kernels (Matsakis &amp; Klock, 2014) utilizing Rayon data parallelism and SIMD vectorization to overcome Python's "
        "Global Interpreter Lock (GIL). Evaluated client-side WebAssembly execution (Haas et al., 2017) running structured Float32Array simulation loops directly in "
        "browser background Web Workers with zero cloud latency.",

        "<b>Pillar 4: Web-Native 3D Telemetry &amp; Scientific Visualization:</b> "
        "Reviewed browser-based visualization engines (Three.js WebGL 2.0 and Kitware's vtk.js / ParaView Glance) for client-side rendering of 3D streamlines, "
        "isocontours, and cutplanes. Evaluated full-duplex WebSocket (RFC 6455) streaming protocols for real-time bi-directional telemetry and residual monitoring.",

        "<b>Pillar 5: Formal Definition of Research Scope &amp; Benchmarking Criteria:</b> "
        "Formulated the operational boundaries of Project UR2627GEN317: focusing on incompressible laminar-to-transitional flows, structured Cartesian grids with "
        "obstacle voxel masking, and automated two-way OpenFOAM dictionary export. Selected canonical validation benchmarks: Ghia et al. (1982) lid-driven cavity "
        "(Re = 100/400) and de Vahl Davis (1983) differentially heated natural convection."
    ]
    for wi in work_items:
        story.append(Paragraph(f"• {wi}", body_style))

    story.append(Spacer(1, 4))

    # SECTION 2: COMPARATIVE MATRIX
    story.append(Paragraph("2. Comparative Evaluation of Existing Literature vs. OpenZess", h2_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#CBD5E1"), spaceBefore=1, spaceAfter=4))

    matrix_data = [
        [Paragraph("Evaluation Criterion", tbl_head_style), Paragraph("Commercial Desktop CFD (ANSYS/COMSOL)", tbl_head_style), Paragraph("OpenFOAM (Native C++)", tbl_head_style), Paragraph("OpenZess (UR2627GEN317)", tbl_head_style)],
        [
            Paragraph("<b>Accessibility &amp; Deployment</b>", tbl_cell_style),
            Paragraph("Proprietary license, heavy workstation install", tbl_cell_style),
            Paragraph("Linux terminal, complex dictionary syntax", tbl_cell_style),
            Paragraph("<b>Zero-install, browser-accessible web studio</b>", tbl_cell_style)
        ],
        [
            Paragraph("<b>Compute Architecture</b>", tbl_cell_style),
            Paragraph("Closed-source C++ solvers", tbl_cell_style),
            Paragraph("Open-source C++ (MPI clusters)", tbl_cell_style),
            Paragraph("<b>Client WASM Worker + Rust SIMD Sidecar</b>", tbl_cell_style)
        ],
        [
            Paragraph("<b>AI / Surrogate Support</b>", tbl_cell_style),
            Paragraph("None / external vendor plugins", tbl_cell_style),
            Paragraph("None (standard numerical solvers only)", tbl_cell_style),
            Paragraph("<b>Sub-50 ms PINN surrogate + AI copilot</b>", tbl_cell_style)
        ],
        [
            Paragraph("<b>3D Visualization</b>", tbl_cell_style),
            Paragraph("Desktop GUI only", tbl_cell_style),
            Paragraph("Offline post-processing in ParaView", tbl_cell_style),
            Paragraph("<b>Live 3D WebGL &amp; ParaView Glance (vtk.js)</b>", tbl_cell_style)
        ],
        [
            Paragraph("<b>Interoperability</b>", tbl_cell_style),
            Paragraph("Proprietary locked formats", tbl_cell_style),
            Paragraph("Standard OpenFOAM case tree", tbl_cell_style),
            Paragraph("<b>Two-way export (OpenFOAM ZIP + VTK)</b>", tbl_cell_style)
        ]
    ]
    matrix_table = Table(matrix_data, colWidths=[95, 140, 140, 148])
    matrix_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F1F5F9")),
        ('BOX', (0,0), (-1,-1), 0.6, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(matrix_table)
    
    # Intentional Page Break to start Page 2 cleanly
    story.append(PageBreak())

    # SECTION 3: SCOPE BOUNDARIES TABLE (Page 2)
    story.append(Paragraph("3. Defined Research Scope &amp; Operational Boundaries", h2_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#CBD5E1"), spaceBefore=1, spaceAfter=4))

    scope_data = [
        [Paragraph("Scope Dimension", tbl_head_style), Paragraph("In-Scope (Supported, Validated &amp; Benchmark-Tested)", tbl_head_style), Paragraph("Out-of-Scope (Explicit Phase Boundaries)", tbl_head_style)],
        [
            Paragraph("<b>Governing Physics</b>", tbl_cell_style),
            Paragraph("• Incompressible 2D/3D Navier-Stokes momentum equations<br/>• Boussinesq thermal buoyancy natural/forced convection<br/>• Thermal energy conduction-diffusion transport", tbl_cell_style),
            Paragraph("• Supersonic compressible flows (Ma &gt; 0.3) with shocks<br/>• Reacting combustion or multi-phase interfaces", tbl_cell_style)
        ],
        [
            Paragraph("<b>Mesh &amp; Domain</b>", tbl_cell_style),
            Paragraph("• Structured Cartesian grids with obstacle voxel masking<br/>• Real-time interactive grid scaling (32&sup2; up to 128&sup2;+)<br/>• Standard Dirichlet &amp; Neumann physical boundary conditions", tbl_cell_style),
            Paragraph("• Unstructured arbitrary polyhedral tetrahedral meshes<br/>• Arbitrary dynamic moving boundary meshes (ALE)", tbl_cell_style)
        ],
        [
            Paragraph("<b>Solver Schemes</b>", tbl_cell_style),
            Paragraph("• Fractional-step Chorin projection method<br/>• Upwind advection + Central differencing diffusion<br/>• Pressure Poisson iterative solvers (Jacobi, GS, Sparse CG)", tbl_cell_style),
            Paragraph("• Multi-phase volume-of-fluid (VOF) surface tracking<br/>• Full acoustic wave propagation models", tbl_cell_style)
        ],
        [
            Paragraph("<b>Execution Modes</b>", tbl_cell_style),
            Paragraph("• Mode 1: Client-Side WebAssembly Solver (Zero server)<br/>• Mode 2: Hybrid Python FastAPI + Rust SIMD Sidecar<br/>• Mode 3: Sub-50 ms Instant Physics-Informed AI Surrogate", tbl_cell_style),
            Paragraph("• Large multi-node MPI supercomputer clusters (Slurm schedulers not required for web workflow)", tbl_cell_style)
        ]
    ]
    scope_table = Table(scope_data, colWidths=[95, 220, 208])
    scope_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F1F5F9")),
        ('BOX', (0,0), (-1,-1), 0.6, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(scope_table)
    story.append(Spacer(1, 6))

    # Verification Benchmarks
    story.append(Paragraph("Benchmark Verification &amp; Validation Protocol", h2_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#CBD5E1"), spaceBefore=1, spaceAfter=4))
    bench_text = (
        "To rigorously validate the numerical accuracy of OpenZess, three canonical reference benchmarks have been established: "
        "(1) <b>Lid-Driven Cavity Flow (Ghia et al., 1982)</b> for u/v centerline velocity profiles at Re = 100 and Re = 400; "
        "(2) <b>Differentially Heated Square Cavity (de Vahl Davis, 1983)</b> for Rayleigh numbers Ra = 10<sup>4</sup> to 10<sup>6</sup>; and "
        "(3) <b>Confined Obstacle Vortex Shedding</b> benchmarked against native OpenFOAM <code>buoyantBoussinesqSimpleFoam</code>."
    )
    story.append(Paragraph(bench_text, body_style))
    story.append(Spacer(1, 6))

    # SECTION 4: KEY REFERENCES
    story.append(Paragraph("4. Key Academic References &amp; Literature Sources", h2_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#CBD5E1"), spaceBefore=1, spaceAfter=3))

    refs = [
        "[1] A. J. Chorin, 'Numerical solution of the Navier-Stokes equations,' <i>Math. Comp.</i>, vol. 22, no. 104, pp. 745–762, 1968.",
        "[2] H. Jasak, 'Error analysis and estimation for the finite volume method with applications to fluid flows,' Ph.D. dissertation, Imperial College, 1996.",
        "[3] H. G. Weller et al., 'A tensorial approach to computational continuum mechanics using object-oriented techniques,' <i>Comput. Phys.</i>, vol. 12, no. 6, pp. 620–631, 1998.",
        "[4] M. Raissi, P. Perdikaris, and G. E. Karniadakis, 'Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear PDEs,' <i>J. Comput. Phys.</i>, vol. 378, pp. 686–707, 2019.",
        "[5] Z. Li et al., 'Fourier neural operator for parametric partial differential equations,' in <i>ICLR</i>, 2021.",
        "[6] S. L. Brunton, B. R. Noack, and P. Koumoutsakos, 'Machine learning for fluid mechanics,' <i>Annu. Rev. Fluid Mech.</i>, vol. 52, pp. 477–508, 2020.",
        "[7] U. Ghia, K. N. Ghia, and C. T. Shin, 'High-Re solutions for incompressible flow using the Navier-Stokes equations and a multigrid method,' <i>J. Comput. Phys.</i>, vol. 48, no. 3, pp. 387–411, 1982.",
        "[8] G. de Vahl Davis, 'Natural convection of air in a square cavity: a bench mark numerical solution,' <i>Int. J. Numer. Meth. Fluids</i>, vol. 3, no. 3, pp. 249–264, 1983.",
        "[9] A. Haas et al., 'Bringing the web up to speed with WebAssembly,' in <i>ACM SIGPLAN Notices</i>, vol. 52, no. 6, pp. 185–200, 2017."
    ]
    for r in refs:
        story.append(Paragraph(r, ParagraphStyle('RefStyle', parent=body_style, fontSize=7, leading=8.8, spaceAfter=1.5)))

    return story

def generate_unified_report(output_paths):
    for p in output_paths:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        doc = SimpleDocTemplate(
            p,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=40,
            bottomMargin=42
        )
        fresh_story = create_story()
        doc.build(fresh_story, canvasmaker=NumberedCanvas)
        print(f"Generated unified report: {p}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_paths = [
        os.path.join(base_dir, "UR2627GEN317_Literature_Review_Report.pdf"),
        os.path.join(base_dir, "UR2627GEN317_Literature_Review_Debjit_Das.pdf"),
        os.path.join(base_dir, "UR2627GEN317_Literature_Review_Anshumaan_Das.pdf"),
        os.path.join(base_dir, "docs", "UR2627GEN317_Literature_Review_Report.pdf"),
        os.path.join(base_dir, "docs", "UR2627GEN317_Literature_Review_Debjit_Das.pdf"),
        os.path.join(base_dir, "docs", "UR2627GEN317_Literature_Review_Anshumaan_Das.pdf"),
    ]
    generate_unified_report(target_paths)
