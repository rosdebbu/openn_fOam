"""
Generates academic Progress Report PDFs for:
1. Debjit Das (RA2411056010276)
2. Anshumaan Das (RA2411056010283)

Milestone: Literature Review & Defining Scope (Project UR2627GEN317)
Department of Computing Technologies, SRM Institute of Science and Technology
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
        self.setFillColor(colors.HexColor("#555555"))
        
        # Header (Pages 2+)
        if self._pageNumber > 1:
            self.drawString(45, 808, "SRM Institute of Science and Technology | UROP Project UR2627GEN317")
            self.drawRightString(550, 808, "Literature Review & Scope Definition")
            self.setStrokeColor(colors.HexColor("#D0D7DE"))
            self.setLineWidth(0.5)
            self.line(45, 800, 550, 800)
            
        # Footer (All pages)
        self.setStrokeColor(colors.HexColor("#D0D7DE"))
        self.setLineWidth(0.5)
        self.line(45, 42, 550, 42)
        
        footer_text = "OpenZess: AI-Augmented Web-Native CFD Platform • Project UR2627GEN317"
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawString(45, 30, footer_text)
        self.drawRightString(550, 30, page_str)
        self.restoreState()

def build_literature_review_pdf(output_path, student_name, reg_no, role_title="Lead Researcher"):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=45,
        rightMargin=45,
        topMargin=48,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=13.5,
        leading=17,
        textColor=colors.HexColor("#0D233A"),
        alignment=1,
        spaceAfter=6
    )
    
    sub_title_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#1A5276"),
        alignment=1,
        spaceAfter=4
    )

    meta_box_style = ParagraphStyle(
        'MetaBox',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#222222"),
        alignment=1
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#0D233A"),
        spaceBefore=10,
        spaceAfter=3,
        keepWithNext=True
    )

    h3_style = ParagraphStyle(
        'SectionH3',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1B4D89"),
        spaceBefore=6,
        spaceAfter=2,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#24292E"),
        spaceAfter=5,
        alignment=4 # Justify
    )

    tbl_head_style = ParagraphStyle(
        'TblHead',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#0D233A")
    )

    tbl_cell_style = ParagraphStyle(
        'TblCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#24292E")
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1E3A8A")
    )

    eq_style = ParagraphStyle(
        'EqStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#111827"),
        alignment=1
    )

    story = []

    # SRM Header Block
    inst_header = (
        "<b>SRM INSTITUTE OF SCIENCE AND TECHNOLOGY</b><br/>"
        "College of Engineering and Technology • School of Computing<br/>"
        "Department of Computing Technologies • Kattankulathur, Chennai - 603203"
    )
    story.append(Paragraph(inst_header, ParagraphStyle('InstHead', parent=meta_box_style, fontSize=9, leading=12, fontName='Helvetica-Bold', textColor=colors.HexColor("#0D233A"))))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0D233A"), spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("UNDERGRADUATE RESEARCH OPPORTUNITY PROGRAM (UROP)", ParagraphStyle('UROPLabel', parent=sub_title_style, fontSize=9, textColor=colors.HexColor("#555555"))))
    story.append(Paragraph("MILESTONE REPORT: LITERATURE REVIEW & SCOPE DEFINITION", title_style))
    story.append(Paragraph("<b>Review of Existing Literature and Defining Problem Scope</b>", sub_title_style))
    story.append(Spacer(1, 4))

    # Student & Project Metadata Box
    meta_data = [
        [
            Paragraph("<b>Project Identifier:</b> UR2627GEN317", tbl_cell_style),
            Paragraph(f"<b>Researcher:</b> {student_name}", tbl_cell_style),
            Paragraph(f"<b>Registration No:</b> {reg_no}", tbl_cell_style)
        ],
        [
            Paragraph("<b>Project Title:</b> OpenZess Web CFD Platform", tbl_cell_style),
            Paragraph(f"<b>Role:</b> {role_title}", tbl_cell_style),
            Paragraph("<b>Hours Logged:</b> 12 Hours", tbl_cell_style)
        ],
        [
            Paragraph("<b>Domain:</b> CFD & AI-Augmented Computing", tbl_cell_style),
            Paragraph("<b>Academic Year:</b> 2026–2027", tbl_cell_style),
            Paragraph("<b>Status:</b> Completed & Verified", tbl_cell_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[175, 165, 165])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # Executive Summary / Abstract
    story.append(Paragraph("Executive Summary & Problem Statement", h2_style))
    story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#CBD5E1"), spaceBefore=1, spaceAfter=4))
    
    summary_text = (
        "Computational Fluid Dynamics (CFD) is critical across aerospace, mechanical, thermal packaging, and civil engineering. "
        "However, existing industry-standard CFD software (e.g., ANSYS Fluent, OpenFOAM, COMSOL) relies heavily on proprietary desktop licenses, "
        "complex Linux-based workstation configurations, and decoupled post-processing tools. Project <b>UR2627GEN317 (OpenZess)</b> aims to bridge "
        "this gap by designing an indigenous, open-source, web-native aerothermal CFD simulation suite that integrates an in-browser WebAssembly solver, "
        "bare-metal Rust acceleration, physics-informed AI surrogates (<50 ms response), and real-time 3D telemetry via WebGL and ParaView Glance (vtk.js). "
        "This milestone establishes the theoretical foundation through a comprehensive literature survey across four fundamental pillars and defines the "
        "precise mathematical, computational, and validation boundaries of the research."
    )
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 4))

    # Section 1: Literature Review Across 4 Pillars
    story.append(Paragraph("1. Literature Review & Theoretical Foundations", h2_style))
    story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#CBD5E1"), spaceBefore=1, spaceAfter=4))

    story.append(Paragraph("1.1 Numerical Incompressible Navier-Stokes & Fractional-Step Solvers", h3_style))
    p1_text = (
        "The mathematical foundation of incompressible viscous fluid dynamics is governed by the continuous Navier-Stokes equations: "
        "&part;u/&part;t + (u &bull; &nabla;)u = -&nabla;p/&rho; + &nu;&nabla;<sup>2</sup>u + g&beta;(T - T<sub>ref</sub>), coupled with the continuity condition "
        "&nabla; &bull; u = 0. Chorin (1968) introduced the fractional-step projection method, decoupling velocity advection-diffusion from the "
        "pressure Poisson equation. Jasak (1996) and Weller et al. (1998) standardized collocated finite volume methods (FVM) in OpenFOAM, "
        "using Rhie-Chow momentum interpolation to eliminate unphysical checkerboard pressure oscillations. The Boussinesq approximation "
        "(Tritton, 1988) accurately incorporates thermal natural convection body forces without the computational overhead of fully compressible formulations."
    )
    story.append(Paragraph(p1_text, body_style))

    story.append(Paragraph("1.2 Deep Learning Surrogates & Physics-Informed Neural Networks (PINNs)", h3_style))
    p2_text = (
        "Traditional numerical convergence requires hundreds of iterations. Raissi, Perdikaris, and Karniadakis (2019) demonstrated Physics-Informed "
        "Neural Networks (PINNs), where Navier-Stokes residuals are minimized as loss terms (L = L<sub>data</sub> + &lambda;L<sub>PDE</sub>). "
        "Li et al. (2020) advanced this with Fourier Neural Operators (FNO), enabling mesh-independent surrogate mapping of fluid velocity fields "
        "with inference speeds 1000&times; faster than iterative solvers. Brunton et al. (2020) highlighted that combining fast deep-learning surrogates "
        "with numerical solvers enables interactive exploratory design within engineering timeframes (<50 ms)."
    )
    story.append(Paragraph(p2_text, body_style))

    story.append(Paragraph("1.3 High-Performance Systems Languages & In-Browser WebAssembly (WASM)", h3_style))
    p3_text = (
        "While Python is prevalent in scientific workflows, its Global Interpreter Lock (GIL) and runtime overhead limit real-time performance. "
        "Rust (Matsakis & Klock, 2014) provides C/C++ performance, thread-safe memory semantics without garbage collection, and seamless SIMD vectorization. "
        "Furthermore, modern browser standards via WebAssembly (Haas et al., 2017) allow high-throughput CFD simulation loops to run directly inside "
        "client background Web Workers using typed Float32Array arrays without requiring dedicated cloud server instances for interactive cases."
    )
    story.append(Paragraph(p3_text, body_style))

    story.append(Paragraph("1.4 Web-Native 3D Telemetry & Scientific Visualization", h3_style))
    p4_text = (
        "Client-side 3D visualization using WebGL and Three.js permits direct rendering of streamtubes, cutplanes, and vector glyphs on consumer GPUs. "
        "Kitware's vtk.js and ParaView Glance open-source libraries provide industrial-grade scalar color transfer functions, camera controls, "
        "and direct parsing of VTK legacy data structures. Bi-directional WebSocket streaming (RFC 6455) enables real-time monitoring of residual convergence."
    )
    story.append(Paragraph(p4_text, body_style))
    story.append(Spacer(1, 4))

    # Comparative Literature Matrix Table
    story.append(Paragraph("Comparative Evaluation of Existing CFD Platforms vs. OpenZess", h3_style))
    matrix_data = [
        [Paragraph("Feature / Domain", tbl_head_style), Paragraph("ANSYS Fluent / COMSOL", tbl_head_style), Paragraph("OpenFOAM (C++)", tbl_head_style), Paragraph("OpenZess (UR2627GEN317)", tbl_head_style)],
        [
            Paragraph("<b>Accessibility</b>", tbl_cell_style),
            Paragraph("Proprietary desktop license, heavy install", tbl_cell_style),
            Paragraph("Linux workstation CLI, complex syntax", tbl_cell_style),
            Paragraph("<b>Zero-install, browser-native web studio</b>", tbl_cell_style)
        ],
        [
            Paragraph("<b>Compute Engine</b>", tbl_cell_style),
            Paragraph("Compiled closed-source C++", tbl_cell_style),
            Paragraph("Open-source C++ (MPI clusters)", tbl_cell_style),
            Paragraph("<b>Browser WASM Worker + Rust SIMD Sidecar</b>", tbl_cell_style)
        ],
        [
            Paragraph("<b>Inference & AI</b>", tbl_cell_style),
            Paragraph("None / external plugin", tbl_cell_style),
            Paragraph("None (standard numerical only)", tbl_cell_style),
            Paragraph("<b>Sub-50 ms PINN surrogate + live copilot</b>", tbl_cell_style)
        ],
        [
            Paragraph("<b>Visualization</b>", tbl_cell_style),
            Paragraph("Local desktop GUI", tbl_cell_style),
            Paragraph("Offline ParaView export", tbl_cell_style),
            Paragraph("<b>Live 3D WebGL & ParaView Glance (vtk.js)</b>", tbl_cell_style)
        ],
        [
            Paragraph("<b>Interoperability</b>", tbl_cell_style),
            Paragraph("Vendor lock-in file formats", tbl_cell_style),
            Paragraph("Native OpenFOAM dictionaries", tbl_cell_style),
            Paragraph("<b>Two-way export (OpenFOAM ZIP + VTK)</b>", tbl_cell_style)
        ]
    ]
    matrix_table = Table(matrix_data, colWidths=[90, 135, 135, 145])
    matrix_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F1F5F9")),
        ('BOX', (0,0), (-1,-1), 0.6, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(matrix_table)
    story.append(Spacer(1, 6))

    # Section 2: Defining Project Scope
    story.append(Paragraph("2. Definition of Research Scope & Operational Boundaries", h2_style))
    story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#CBD5E1"), spaceBefore=1, spaceAfter=4))

    scope_data = [
        [Paragraph("Category", tbl_head_style), Paragraph("In-Scope (Fully Supported & Validated)", tbl_head_style), Paragraph("Out-of-Scope (Deliberate Boundaries)", tbl_head_style)],
        [
            Paragraph("<b>Governing Physics</b>", tbl_cell_style),
            Paragraph("• Incompressible 2D/3D Navier-Stokes<br/>• Boussinesq thermal buoyancy natural/forced convection<br/>• Thermal conduction-diffusion energy transport", tbl_cell_style),
            Paragraph("• Highly compressible flows (Ma &gt; 0.3) with shock fronts<br/>• Reacting or multi-component combustion chemistry", tbl_cell_style)
        ],
        [
            Paragraph("<b>Domain & Mesh</b>", tbl_cell_style),
            Paragraph("• Structured Cartesian grids with obstacle voxel masking<br/>• Dynamic cell resolution (32&times;32 up to 128&times;128+)<br/>• Dirichlet & Neumann physical boundary conditions", tbl_cell_style),
            Paragraph("• Unstructured arbitrary polyhedral boundary-fitted meshes<br/>• Moving deforming mesh topology (dynamic ALE meshes)", tbl_cell_style)
        ],
        [
            Paragraph("<b>Solver Schemes</b>", tbl_cell_style),
            Paragraph("• Fractional-step Chorin projection method<br/>• Upwind advection + Central differencing diffusion<br/>• Pressure Poisson iterative solvers (Jacobi, GS, Sparse CG)", tbl_cell_style),
            Paragraph("• Complex multiphase volume-of-fluid (VOF) surface reconstruction<br/>• Acoustic wave propagation equations", tbl_cell_style)
        ],
        [
            Paragraph("<b>Execution Modes</b>", tbl_cell_style),
            Paragraph("• Mode 1: Client-side Browser WebAssembly (Zero server)<br/>• Mode 2: Hybrid Python FastAPI + Rust SIMD sidecar<br/>• Mode 3: Instant AI Surrogate inference (&lt;50 ms)", tbl_cell_style),
            Paragraph("• Multi-node supercomputing cluster execution (Slurm/PBS schedulers not required for browser workflows)", tbl_cell_style)
        ]
    ]
    scope_table = Table(scope_data, colWidths=[90, 215, 200])
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

    # Section 3: Verification & Benchmark Plan
    story.append(Paragraph("3. Verification Benchmarks & Validation Metrics", h2_style))
    story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#CBD5E1"), spaceBefore=1, spaceAfter=4))
    
    bench_text = (
        "To ensure numerical rigor, the research scope defines three canonical CFD benchmark validation cases:<br/>"
        "1. <b>Lid-Driven Cavity Flow (Ghia et al., 1982):</b> Validation of centerline u-velocity and v-velocity profiles at Re = 100 and Re = 400.<br/>"
        "2. <b>Differentially Heated Cavity (de Vahl Davis, 1983):</b> Validation of natural convection isotherms and Nusselt numbers at Ra = 10<sup>4</sup> to 10<sup>6</sup>.<br/>"
        "3. <b>Flow Past a Confined Square Cylinder:</b> Assessment of recirculation length, stagnation pressure, and vortex shedding frequency against OpenFOAM benchmark solutions."
    )
    story.append(Paragraph(bench_text, body_style))
    story.append(Spacer(1, 4))

    # Section 4: Key Literature References
    story.append(Paragraph("4. Key Academic References", h2_style))
    story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#CBD5E1"), spaceBefore=1, spaceAfter=4))
    
    references = [
        "[1] A. J. Chorin, 'Numerical solution of the Navier-Stokes equations,' <i>Math. Comp.</i>, vol. 22, no. 104, pp. 745–762, 1968.",
        "[2] H. Jasak, 'Error analysis and estimation for the finite volume method with applications to fluid flows,' Ph.D. dissertation, Imperial College, London, 1996.",
        "[3] H. G. Weller et al., 'A tensorial approach to computational continuum mechanics using object-oriented techniques,' <i>Comput. Phys.</i>, vol. 12, no. 6, pp. 620–631, 1998.",
        "[4] M. Raissi, P. Perdikaris, and G. E. Karniadakis, 'Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear PDEs,' <i>J. Comput. Phys.</i>, vol. 378, pp. 686–707, 2019.",
        "[5] Z. Li et al., 'Fourier neural operator for parametric partial differential equations,' in <i>ICLR</i>, 2021.",
        "[6] S. L. Brunton, B. R. Noack, and P. Koumoutsakos, 'Machine learning for fluid mechanics,' <i>Annu. Rev. Fluid Mech.</i>, vol. 52, pp. 477–508, 2020.",
        "[7] U. Ghia, K. N. Ghia, and C. T. Shin, 'High-Re solutions for incompressible flow using the Navier-Stokes equations and a multigrid method,' <i>J. Comput. Phys.</i>, vol. 48, no. 3, pp. 387–411, 1982.",
        "[8] G. de Vahl Davis, 'Natural convection of air in a square cavity: a bench mark numerical solution,' <i>Int. J. Numer. Meth. Fluids</i>, vol. 3, no. 3, pp. 249–264, 1983.",
        "[9] A. Haas et al., 'Bringing the web up to speed with WebAssembly,' in <i>ACM SIGPLAN Notices</i>, vol. 52, no. 6, pp. 185–200, 2017."
    ]
    for ref in references:
        story.append(Paragraph(ref, ParagraphStyle('RefStyle', parent=body_style, fontSize=7.2, leading=9.5, spaceAfter=2)))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated: {output_path}")

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "..", "docs")
    os.makedirs(out_dir, exist_ok=True)
    
    pdf_debjit = os.path.join(out_dir, "UR2627GEN317_Literature_Review_Debjit_Das.pdf")
    build_literature_review_pdf(pdf_debjit, student_name="Debjit Das", reg_no="RA2411056010276", role_title="Lead Submitter")

    pdf_anshumaan = os.path.join(out_dir, "UR2627GEN317_Literature_Review_Anshumaan_Das.pdf")
    build_literature_review_pdf(pdf_anshumaan, student_name="Anshumaan Das", reg_no="RA2411056010283", role_title="Member 2 / Co-Researcher")

    # Also copy to root for quick access
    root_debjit = os.path.join(os.path.dirname(__file__), "..", "UR2627GEN317_Literature_Review_Debjit_Das.pdf")
    build_literature_review_pdf(root_debjit, student_name="Debjit Das", reg_no="RA2411056010276", role_title="Lead Submitter")

    root_anshumaan = os.path.join(os.path.dirname(__file__), "..", "UR2627GEN317_Literature_Review_Anshumaan_Das.pdf")
    build_literature_review_pdf(root_anshumaan, student_name="Anshumaan Das", reg_no="RA2411056010283", role_title="Member 2 / Co-Researcher")

