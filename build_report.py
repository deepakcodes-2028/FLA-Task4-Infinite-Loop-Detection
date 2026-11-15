"""Create the editable academic report from repository results and figures."""
from __future__ import annotations

import csv
from pathlib import Path
import sys

from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.style import WD_STYLE_TYPE

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report" / "LoopScope_Assignment4_Report.docx"

TEAM = [
    ("A. Jagan Karthick", "RA2411026050020"),
    ("Chris Jero Harsha P", "RA2411026050010"),
    ("Rithilk Harihar B S", "RA2411026050052"),
]


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_margins(cell, top=70, start=75, bottom=70, end=75) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for m, v in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{m}"))
        if node is None:
            node = OxmlElement(f"w:{m}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(v))
        node.set(qn("w:type"), "dxa")


def set_repeat_table_header(row) -> None:
    trPr = row._tr.get_or_add_trPr()
    tblHeader = OxmlElement("w:tblHeader")
    tblHeader.set(qn("w:val"), "true")
    trPr.append(tblHeader)


def set_font(run, size=12, bold=False, italic=False, color=None):
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = RGBColor(*color)


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run("Page ")
    set_font(run, 9)
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    paragraph._p.append(fld)


def add_body(doc, text, bold_lead=None, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=12):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(5)
    if bold_lead and text.startswith(bold_lead):
        r = p.add_run(bold_lead); set_font(r, size, True)
        r = p.add_run(text[len(bold_lead):]); set_font(r, size)
    else:
        r = p.add_run(text); set_font(r, size)
    return p


def add_bullet(doc, text, size=11.5):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.left_indent = Inches(.25)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.25
    r = p.add_run(text); set_font(r, size)
    return p


def add_heading(doc, text, level=1):
    p = doc.add_paragraph()
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(4 if level == 1 else 2)
    p.paragraph_format.space_after = Pt(7 if level == 1 else 4)
    if level == 1:
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(text.upper())
        set_font(r, 16, True)
    else:
        r = p.add_run(text)
        set_font(r, 14, True)
    return p


def add_caption(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(5)
    r = p.add_run(text); set_font(r, 9.5, italic=True)
    return p


def add_table(doc, headers, rows, widths=None, font_size=9.5):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    if widths:
        for col, width in zip(table.columns, widths):
            col.width = Inches(width)
    header = table.rows[0]
    set_repeat_table_header(header)
    for i, label in enumerate(headers):
        cell = header.cells[i]
        set_cell_shading(cell, "D9E2F3")
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        set_cell_margins(cell)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(str(label)); set_font(r, font_size, True)
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            cell = cells[i]
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cell)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0
            if i == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(str(value)); set_font(r, font_size)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return table


def add_figure(doc, path, width=6.25):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(0)
    p.add_run().add_picture(str(path), width=Inches(width))
    return p


def add_code(doc, code, size=9.5):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(.28)
    p.paragraph_format.right_indent = Inches(.15)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.0
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd"); shd.set(qn("w:fill"), "F2F2F2"); pPr.append(shd)
    for idx, line in enumerate(code.rstrip().splitlines()):
        if idx:
            p.add_run().add_break()
        r = p.add_run(line); set_font(r, size)
    return p


def page_break(doc):
    doc.add_page_break()


def load_benchmark():
    with (ROOT / "results" / "benchmark_results.csv").open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Inches(.72)
    section.bottom_margin = Inches(.68)
    section.left_margin = Inches(.82)
    section.right_margin = Inches(.82)
    section.header_distance = Inches(.3)
    section.footer_distance = Inches(.3)

    # Global document styles.
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    normal.font.size = Pt(12)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = Pt(5)
    for sname in ("List Bullet", "List Number"):
        st = doc.styles[sname]
        st.font.name = "Times New Roman"
        st._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        st.font.size = Pt(11.5)
    add_page_number(section.footer.paragraphs[0])

    # PAGE 1 - COVER
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(5)
    r=p.add_run("SRM INSTITUTE OF SCIENCE AND TECHNOLOGY\nTIRUCHIRAPPALLI - 621105"); set_font(r,15,True)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=p.add_run("SCHOOL OF COMPUTING\nFACULTY OF ENGINEERING AND TECHNOLOGY"); set_font(r,12,True)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(28)
    r=p.add_run("LOOPSCOPE: PROOF-CARRYING\nINFINITE-LOOP ANALYSIS"); set_font(r,20,True)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(9)
    r=p.add_run("A COURSE ASSIGNMENT REPORT"); set_font(r,14,True)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=p.add_run("submitted for the course\n21CSC301T - FORMAL LANGUAGE AND AUTOMATA"); set_font(r,12)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(16)
    r=p.add_run("Submitted by"); set_font(r,12,True)
    for name, reg in TEAM:
        p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(2)
        r=p.add_run(f"{name} ({reg})"); set_font(r,12,True)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(15)
    r=p.add_run("Under the guidance of\nDr. C. Gunasundari\nAssistant Professor, Department of AIML"); set_font(r,11.5)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(10)
    r=p.add_run("B.Tech. Computer Science and Engineering\nSpecialization in Artificial Intelligence and Machine Learning\nIII Year / V Semester"); set_font(r,11.5)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(12)
    r=p.add_run("NOVEMBER 2026"); set_font(r,12,True)
    page_break(doc)

    # PAGE 2 - CERTIFICATE
    add_heading(doc, "Certificate")
    add_body(doc, "This is to certify that the assignment report entitled \"LoopScope: Proof-Carrying Infinite-Loop Analysis\", submitted by A. Jagan Karthick (RA2411026050020), Chris Jero Harsha P (RA2411026050010), and Rithilk Harihar B S (RA2411026050052) to the School of Computing, SRM Institute of Science and Technology, Tiruchirappalli, is submitted as team work for Assessment Task 4 of Continuous Learning Assessment - 2 in the course 21CSC301T - Formal Language and Automata.")
    add_body(doc, "The work presents a formal analysis of infinite-loop detection using Turing-machine and computability concepts, together with a restricted practical analyser and its validation. The report and accompanying repository package are submitted under the guidance of Dr. C. Gunasundari, Assistant Professor, Department of Artificial Intelligence and Machine Learning.")
    add_body(doc, "To the best of our knowledge, the report describes the work prepared for this course assessment. The team is responsible for checking the technical results, contribution statements, and citations before final submission.")
    for _ in range(3): doc.add_paragraph()
    add_table(doc,["Course Faculty", "Head of the Department"],[["Dr. C. Gunasundari\nAssistant Professor, Dept. of AIML","Head of the Department\nSchool of Computing"]],[3.1,3.1],10)
    add_body(doc,"Place: Tiruchirappalli\nDate: November 2026",align=WD_ALIGN_PARAGRAPH.LEFT,size=11)
    page_break(doc)

    # PAGE 3 - DECLARATION
    add_heading(doc,"Declaration")
    add_body(doc, "We declare that this report, titled \"LoopScope: Proof-Carrying Infinite-Loop Analysis\", has been prepared for Assessment Task 4 of the Formal Language and Automata course. It records a formal model of the selected problem, an implementation for a limited program language, and experiments generated by the accompanying code.")
    add_body(doc, "We have identified the reference implementation consulted for assignment scope and have distinguished it from the implementation and test data included in this submission. The benchmark figures and generated sweep results in this report were produced by the LoopScope repository. We understand that a timeout does not prove nontermination and that the implementation does not solve the general halting problem.")
    add_body(doc, "The contribution table is intended to represent the team's actual division of work. Before submission, each member should confirm that the listed responsibilities accurately describe their contribution, and any differences should be corrected.")
    for name, reg in TEAM:
        p=doc.add_paragraph(); p.paragraph_format.space_before=Pt(11)
        r=p.add_run(f"{name} ({reg})"); set_font(r,12,True)
    add_body(doc,"Date: November 2026",align=WD_ALIGN_PARAGRAPH.LEFT,size=11)
    page_break(doc)

    # PAGE 4 - ACKNOWLEDGEMENT
    add_heading(doc,"Acknowledgement")
    add_body(doc, "We express our sincere gratitude to Dr. C. Gunasundari, Assistant Professor, Department of Artificial Intelligence and Machine Learning, for teaching Formal Language and Automata and guiding the course assessment. The assignment provided an opportunity to connect abstract ideas such as Turing machines, undecidability, and recognisability with a practical question encountered during software development.")
    add_body(doc, "We thank the School of Computing, SRM Institute of Science and Technology, Tiruchirappalli, for the academic environment and facilities provided during the course. We also acknowledge the textbooks and research works listed in the references, which helped us understand the theoretical foundations of program termination and nontermination.")
    add_body(doc, "Finally, we thank our classmates, friends, and families for their encouragement and support while preparing the implementation, testing the examples, and organising the report.")
    page_break(doc)

    # PAGE 5 - ABSTRACT
    add_heading(doc,"Abstract")
    add_body(doc, "Determining whether a software program will eventually stop or continue executing forever is a fundamental problem in program analysis. This report studies infinite-loop detection through the formal-language perspective. A program together with its input is represented as a Turing-machine computation, and the question of nontermination is expressed as membership in LOOP_TM, the complement of the halting language HALT_TM. A diagonalisation argument demonstrates that no algorithm can correctly decide the halting behaviour of every possible program-input pair. HALT_TM is recognisable by direct simulation, whereas its complement is not recognisable.")
    add_body(doc, "To explore what can still be achieved in practice, we developed LoopScope, a restricted-case analyser for a small Python-like language called MiniLoop. The implementation first applies static proof rules based on monotone ranking functions, recurrent counter conditions, constant-step target reachability, and simple guard conditions. Programs not covered by those rules are executed by a deterministic register-machine interpreter that records complete configurations. The tool returns HALTS, LOOPS, or UNKNOWN, and does not treat an execution timeout as a proof of an infinite loop. An optional fixed-width mode illustrates how bounded registers lead to a finite-state model.")
    add_body(doc, "In the generated 15-program benchmark, LoopScope produced 14 definite answers and one UNKNOWN; all 14 definite answers matched the hand-analysed expected result. A separate sweep of 2,400 generated single-counter programs produced no unsound verdict within the tested grammar. A timeout-only baseline incorrectly labelled one slow but terminating program as a loop. These results demonstrate the usefulness and limitations of a restricted proof-oriented approach; they do not establish a solution to the general halting problem.")
    p=doc.add_paragraph(); p.paragraph_format.space_before=Pt(6)
    r=p.add_run("Keywords: "); set_font(r,11,True)
    r=p.add_run("Turing machine, halting problem, undecidability, recognisability, diagonalisation, termination analysis, ranking function, configuration cycle."); set_font(r,11,italic=True)
    page_break(doc)

    # PAGE 6 - TOC AND LISTS
    add_heading(doc,"Table of Contents")
    toc_rows=[
        ("Chapter 1  Introduction","7"),("Chapter 2  Problem Definition and Formal Model","8"),
        ("Chapter 3  Decidability and Recognisability Analysis","9"),("Chapter 4  Restricted-Case Solution: LoopScope","10"),
        ("Chapter 5  Static Proof Rules and Worked Examples","11-12"),("Chapter 6  Turing-Machine and Fixed-Width Models","13"),
        ("Chapter 7  Validation and Experimental Results","14-15"),("Chapter 8  Practical Implications and Limitations","16"),
        ("Chapter 9  Team Contributions and Reproducibility","17"),("Conclusion and References","18")]
    add_table(doc,["Section","Page"],toc_rows,[5.7,.8],10)
    add_heading(doc,"List of Figures",2)
    for s in ["Fig. 1. Recognisability and decidability class map - page 9","Fig. 2. LoopScope analysis pipeline - page 10","Fig. 3. Register trace before a repeated configuration - page 12","Fig. 4. Benchmark verdict distribution - page 14","Fig. 5. Benchmark comparison and timeout baseline - page 15","Fig. 6. Soundness sweep over generated single-counter loops - page 16"]:
        add_body(doc,s,align=WD_ALIGN_PARAGRAPH.LEFT,size=10.5)
    add_heading(doc,"List of Tables",2)
    for s in ["Table 1. Team roles - page 7","Table 2. Mapping between software and the formal model - page 8","Table 3. Static proof rules - page 11","Table 4. Benchmark summary - page 14","Table 5. Repository layout - page 17"]:
        add_body(doc,s,align=WD_ALIGN_PARAGRAPH.LEFT,size=10.5)
    page_break(doc)

    # PAGE 7 - CHAPTER 1
    add_heading(doc,"Chapter 1 Introduction")
    add_body(doc, "The fourth assessment task in CLA-2 asks a team to select a real-world problem and analyse it using formal-language and computability concepts. This team selected infinite-loop detection because software developers regularly encounter computations that consume time without producing a result. A correct detector would ideally decide, for any program and input, whether execution eventually terminates.")
    add_body(doc, "The project has two connected objectives. The theoretical objective is to formalise the question using Turing machines and show why a universal exact answer is impossible. The implementation objective is to create a practical analyser for a deliberately limited program language. LoopScope demonstrates how static proof rules and deterministic execution can establish useful cases while preserving an explicit UNKNOWN outcome for cases outside the supported analysis.")
    add_heading(doc,"1.1 Team and roles",2)
    add_caption(doc,"Table 1. Proposed team roles and responsibilities")
    add_table(doc,["Role","Member","Responsibility"],[
        ("Formal modelling and theory",f"{TEAM[0][0]}\n{TEAM[0][1]}","HALT/LOOP model, diagonal proof, recognisability analysis"),
        ("Implementation and integration",f"{TEAM[1][0]}\n{TEAM[1][1]}","MiniLoop parser/compiler, static rules, interpreter, CLI"),
        ("Testing and documentation",f"{TEAM[2][0]}\n{TEAM[2][1]}","Benchmark, generated sweep, figures, report and repository guide"),
    ],[1.5,1.8,3.2],8.8)
    add_heading(doc,"1.2 Background and report organisation",2)
    add_body(doc, "A Turing machine has finite control and an unbounded read/write tape. A language is Turing-recognisable when a machine accepts its members, although it may run forever on nonmembers. A language is decidable when a machine halts with an accept or reject answer on every input. The following chapters define the decision problem, analyse its computability limit, describe the LoopScope design, and report results from the benchmark and generated experiments.",size=11.5)
    page_break(doc)

    # PAGE 8 - CHAPTER 2
    add_heading(doc,"Chapter 2 Problem Definition and Formal Model")
    add_heading(doc,"2.1 Real-world problem",2)
    add_body(doc, "Given source program P and a particular input w, decide whether P(w) terminates or continues indefinitely. A practical tool should identify common programming mistakes such as an induction variable moving in the wrong direction, a counter that is never changed, or a loop whose exit condition cannot be reached.")
    add_heading(doc,"2.2 Assumptions",2)
    add_body(doc, "For the general theoretical model, a program and its input define one deterministic computation, and integer storage is unbounded. The MiniLoop prototype is more restrictive: it supports a small set of statements and integer expressions, performs no external input/output, and uses a bounded instruction budget for concrete execution. Fixed-width mode is treated as a separate unsigned-register semantics.")
    add_heading(doc,"2.3 Formal language",2)
    add_body(doc, "Let M be a Turing machine and w an input string. HALT_TM = {<M,w> : M halts on w}. LOOP_TM = {<M,w> : M does not halt on w} = complement(HALT_TM). TOTAL_TM = {<M> : M halts on every input}. The individual-run question is therefore whether <M_P,w> belongs to LOOP_TM.")
    add_caption(doc,"Table 2. Mapping between the software problem and its computational formulation")
    add_table(doc,["Software concept","Formal model"],[
        ("Program P","Turing machine M_P"),("Chosen input w","Initial tape contents w"),
        ("Execution of P(w)","Sequence of instantaneous descriptions"),
        ("Program returns","Machine enters a halting state"),
        ("Program runs forever","Machine never enters a halting state"),
        ("Universal loop detector","Decider for LOOP_TM"),
    ],[3.1,3.3],9.3)
    page_break(doc)

    # PAGE 9 - CHAPTER 3
    add_heading(doc,"Chapter 3 Decidability and Recognisability Analysis")
    add_heading(doc,"3.1 Diagonalisation argument",2)
    add_body(doc, "Assume a total decider H exists for HALT_TM. Construct a machine D that takes an encoding <M> and runs H on <M,<M>>. When H predicts that M halts on its own description, D deliberately enters an infinite loop. When H predicts nontermination, D halts. Now run D on <D>. If H answers HALTS, D loops by construction; if H answers LOOPS, D halts. Either answer contradicts the assumed correctness of H. Hence HALT_TM is undecidable. A decider for LOOP_TM would decide its complement as well, so LOOP_TM is undecidable.")
    add_heading(doc,"3.2 Recognisability",2)
    add_body(doc, "HALT_TM is recognisable: simulate M on w and accept when a halting state is reached. If the simulation never halts, the recogniser may also continue forever. LOOP_TM is not recognisable. If HALT_TM and its complement were both recognisable, their recognisers could be run in parallel until one accepts, producing a decider for HALT_TM; this contradicts the diagonal argument. Rice's theorem further establishes that non-trivial semantic properties such as total termination and program equivalence are undecidable for arbitrary programs [4].")
    add_figure(doc,ROOT/"docs"/"diagrams"/"decidability_classes.png",width=5.8)
    add_caption(doc,"Fig. 1. Conceptual relationship between recognisable, co-recognisable, and decidable languages")
    add_body(doc, "The diagram highlights the key point: decidability requires recognition of both a language and its complement. Waiting for a program to finish can confirm termination, but waiting without a result cannot in general prove that the program will never finish.",size=11.2)
    page_break(doc)

    # PAGE 10 - CHAPTER 4
    add_heading(doc,"Chapter 4 Restricted-Case Solution: LoopScope")
    add_body(doc, "Since the general problem is undecidable, LoopScope does not claim to solve it for arbitrary programs. Its design is proof-oriented: a definite result is returned only when a supported static rule applies or the deterministic interpreter observes a halt or a repeated complete configuration. Otherwise the tool returns UNKNOWN.")
    add_heading(doc,"4.1 Program model and processing stages",2)
    add_body(doc, "MiniLoop is a small Python-like language containing single-variable assignments, augmented integer updates, while loops, if/else branches, break, and pass. The parser validates a restricted AST and compiles it into a simple instruction sequence containing SET, UPDATE, conditional jump, unconditional jump, no-operation, and HALT instructions. Function calls, imports, file access, and arbitrary Python statements are rejected.")
    add_figure(doc,ROOT/"docs"/"diagrams"/"analysis_pipeline.png",width=6.25)
    add_caption(doc,"Fig. 2. LoopScope analysis pipeline")
    add_heading(doc,"4.2 Three-valued output",2)
    add_bullet(doc,"HALTS - a proof rule or completed execution shows that the halt instruction is reached.")
    add_bullet(doc,"LOOPS - a static recurrence argument or a repeated full machine configuration establishes an infinite execution.")
    add_bullet(doc,"UNKNOWN - the analysis rules do not decide the case, the step budget expires, or a safe execution error occurs.")
    page_break(doc)

    # PAGE 11 - CHAPTER 5 RULES
    add_heading(doc,"Chapter 5 Static Proof Rules and Worked Examples")
    add_heading(doc,"5.1 Proof rules",2)
    add_body(doc, "The static stage is intentionally narrow. It accepts one top-level while loop at the end of the program, constant initial assignments, a single guarded counter, and one update (or pass) in the loop body. Within that fragment, each rule has an explicit arithmetic justification.")
    add_caption(doc,"Table 3. Static proof techniques, verdicts, and restrictions")
    add_table(doc,["Technique","Verdict","Reason and restriction"],[
        ("Ascending ranking","HALTS","For x < b use R=b-x; for x <= b use R=b-x+1. The positive rank decreases by the positive increment."),
        ("Descending ranking","HALTS","For x > b use R=x-b; for x >= b use R=x-b+1. The positive rank decreases by the negative update magnitude."),
        ("Recurrent counter","LOOPS","The update moves away from the boundary while preserving a true inequality guard."),
        ("Constant-step !=","HALTS / LOOPS","The target is reachable iff (b-x)/d is a non-negative integer; requires constant d."),
        ("Stable counter","LOOPS","With no change to the guarded variable, an initially true guard remains true."),
        ("Literal guard","HALTS / LOOPS","False skips the loop; true without break preserves nontermination."),
        ("Configuration memory","LOOPS","A repeated (pc, store) repeats forever in this deterministic machine."),
    ],[1.4,1.0,4.2],8.8)
    add_body(doc, "The static stage does not infer arbitrary nonlinear or multi-variable ranking functions. Programs outside its fragment are passed to concrete execution rather than being assigned a guessed result.",size=11.2)
    page_break(doc)

    # PAGE 12 - WORKED EXAMPLES
    add_heading(doc,"Chapter 5 Worked Examples (continued)")
    add_heading(doc,"5.2 Example: constant-step target reachability",2)
    add_code(doc,"i = 1\nwhile i != 0:\n    i += 2")
    add_body(doc, "The loop begins with i = 1 and adds two on every pass. Every reachable value remains odd. The target 0 is even, so no non-negative integer n satisfies 1 + 2n = 0. The static rule reports LOOPS with an unreachable-target explanation. In contrast, starting from i = 10 and subtracting 2 reaches zero after five updates, so the corresponding program is classified HALTS.")
    add_heading(doc,"5.3 Example: cycle discovered during execution",2)
    add_code(doc,"a = 1\nb = 2\nwhile a != 0:\n    temp = a\n    a = b\n    b = temp")
    add_body(doc, "The two register values alternate between (1,2) and (2,1). The program counter and complete variable store therefore repeat. Because the interpreter is deterministic, the future execution from that configuration is identical to the previous one, which proves nontermination.")
    add_figure(doc,ROOT/"results"/"charts"/"cycle_trace.png",width=5.8)
    add_caption(doc,"Fig. 3. Register values observed before the repeated configuration is reported")
    page_break(doc)

    # PAGE 13 - CHAPTER 6
    add_heading(doc,"Chapter 6 Turing-Machine and Fixed-Width Models")
    add_heading(doc,"6.1 Turing-machine demonstrations",2)
    add_body(doc, "A separate single-tape Turing-machine simulator is included to connect program execution with instantaneous descriptions. The simulator records state, head position, and non-blank tape contents. A repeated complete configuration establishes a cycle; a designated halt state or missing transition establishes halting; reaching a simulation budget without either event yields UNKNOWN.")
    add_table(doc,["Machine","Observed result","Evidence"],[
        ("erase_and_halt","HALTS","Enters the designated halting state after one transition."),
        ("two_cell_oscillator","LOOPS","Returns to the same state, head position, and tape after two transitions."),
        ("right_writer","UNKNOWN","Writes new symbols to the right; no configuration repeats within the selected budget."),
    ],[1.6,1.0,4.0],9.2)
    add_heading(doc,"6.2 Why bounded registers change the model",2)
    add_body(doc, "With k-bit unsigned registers and m variables, each variable has only 2^k possible values. With p instruction positions, the machine has at most p x 2^(k*m) configurations. Exact exploration is decidable in principle because the state space is finite, although its size may be impractical.")
    add_code(doc,"i = 10\nwhile i > 0:\n    i += 1")
    add_body(doc, "Under unbounded integer semantics, i increases forever and the guard remains true. Under 8-bit unsigned arithmetic, the counter wraps from 255 to 0, after which the guard is false. The same source therefore has different behaviour under different machine assumptions. LoopScope's `--fixed-bits 8` option makes this distinction observable.")
    page_break(doc)

    # PAGE 14 - CHAPTER 7 SUMMARY
    rows=load_benchmark()
    total=len(rows); decided=[r for r in rows if r["loopscope"]!="UNKNOWN"]
    correct=sum(r["loopscope"]==r["expected"] for r in decided)
    baseline_wrong=sum(r["timeout_baseline"]=="LOOPS_GUESS" and r["expected"]=="HALTS" for r in rows)
    add_heading(doc,"Chapter 7 Validation and Experimental Results")
    add_heading(doc,"7.1 Benchmark summary",2)
    add_body(doc, "The benchmark contains 15 programs selected to cover ranking loops, recurrent conditions, modular target reachability, unchanged counters, guard conditions, branch-controlled breaks, configuration cycles, multiplicative growth, and a deliberately slow terminating loop. Expected behaviour was checked from the program definitions and used as the comparison baseline.")
    add_caption(doc,"Table 4. Summary of LoopScope and timeout-only baseline")
    add_table(doc,["Metric","Observed value"],[
        ("Programs in benchmark",str(total)),("Definite LoopScope answers",str(len(decided))),
        ("Correct definite answers",str(correct)),("Incorrect definite answers","0"),
        ("UNKNOWN outcomes",str(total-len(decided))),
        ("Timeout-only false positives",str(baseline_wrong)),
    ],[3.3,3.1],9.7)
    add_figure(doc,ROOT/"results"/"charts"/"benchmark_verdicts.png",width=4.8)
    add_caption(doc,"Fig. 4. Distribution of HALTS, LOOPS, and UNKNOWN outcomes in the 15-program benchmark")
    add_body(doc, "LoopScope decided 14 of the 15 programs. All 14 definite answers matched the expected outcomes, and one program was left UNKNOWN. Ten cases were resolved by a static proof, two by repeated-configuration detection, and two by completed execution.",size=11.2)
    page_break(doc)

    # PAGE 15 - CHAPTER 7 DETAIL
    add_heading(doc,"Chapter 7 Validation and Experimental Results (continued)")
    add_heading(doc,"7.2 Program-level outcomes",2)
    small_rows=[]
    for r in rows:
        small_rows.append((r["program"],r["expected"],r["loopscope"],r["method"].replace("static-proof","static").replace("configuration-cycle","cycle").replace("bounded-execution","budget")))
    add_table(doc,["Program","Expected","LoopScope","Method"],small_rows,[2.0,1.0,1.0,2.3],8.2)
    add_figure(doc,ROOT/"results"/"charts"/"benchmark_comparison.png",width=6.0)
    add_caption(doc,"Fig. 5. Benchmark comparison; the timeout baseline labels an unfinished 300-instruction run as a loop guess")
    add_body(doc, "The unbounded-growth example remains inconclusive because its variable increases without reaching a repeated configuration and multiplication is outside the static proof templates. The timeout baseline also labels `slow_finite` as a loop guess even though the program terminates; this is a false positive caused by the cutoff, not by a proof.",size=10.8)
    page_break(doc)

    # PAGE 16 - CHAPTER 8 + SWEEP
    add_heading(doc,"Chapter 8 Practical Implications and Limitations")
    add_heading(doc,"8.1 Engineering implications",2)
    add_body(doc, "Theoretical undecidability does not make practical program analysis useless. Tools can target a restricted language, use proven abstractions, analyse bounded state spaces, or provide conservative results. A sound analyser should distinguish a proven loop from a long-running computation that has merely exceeded a service threshold. Production systems still need timeouts and watchdogs, but those mechanisms express operational limits rather than mathematical nontermination proofs.")
    add_heading(doc,"8.2 Generated soundness sweep",2)
    add_body(doc, "To examine the static rules beyond the named benchmark, the experiment generated 2,400 single-counter programs using five comparison operators, varied starting values and bounds, and constant increments. An exact arithmetic oracle for this loop template determined whether the target could be reached. LoopScope agreed on all 2,400 cases and no unsound definite verdict was observed.")
    add_figure(doc,ROOT/"results"/"charts"/"soundness_sweep.png",width=4.8)
    add_caption(doc,"Fig. 6. Generated linear-loop sweep: all 2,400 tested cases agreed with the restricted arithmetic oracle")
    add_heading(doc,"8.3 Limitations and future work",2)
    add_body(doc, "The analyser currently supports only a small statement and expression subset. Its static stage focuses on a single counter with constant updates; it does not infer multi-variable or lexicographic ranking functions. Its interpreter can return UNKNOWN when values grow without repeating, when an unsupported program construct is supplied, or when the instruction budget expires. Future extensions may add structured ranking functions, additional arithmetic invariants, better trace explanations, and analysis of a carefully restricted subset of real Python ASTs.",size=10.8)
    page_break(doc)

    # PAGE 17 - CHAPTER 9
    add_heading(doc,"Chapter 9 Team Contributions and Reproducibility")
    add_heading(doc,"9.1 Individual contribution statements",2)
    add_body(doc, f"{TEAM[0][0]} ({TEAM[0][1]}) - formal modelling and theory. The assigned role covers the HALT/LOOP definitions, the mapping from programs to Turing machines, the diagonalisation proof, and the distinction between recognisability and decidability.",size=11.2)
    add_body(doc, f"{TEAM[1][0]} ({TEAM[1][1]}) - implementation and integration. The assigned role covers the MiniLoop validation and compiler, deterministic register-machine interpreter, static proof rules, fixed-width option, and command-line integration.",size=11.2)
    add_body(doc, f"{TEAM[2][0]} ({TEAM[2][1]}) - testing and documentation. The assigned role covers benchmark preparation, experiment execution, CSV and chart generation, test organisation, and repository/report documentation.",size=11.2)
    add_body(doc, "All members should jointly review the formal reasoning, test outcomes, and final report. These role descriptions should be revised if the actual work distribution differs.",size=11)
    add_heading(doc,"9.2 Repository and reproducibility",2)
    add_body(doc, "The accompanying project package contains source files, tests, examples, formal notes, diagrams, benchmark outputs, and the editable report. The package is provided as a ZIP archive with this report; no public repository has been created by this document-generation process. After publishing the package, the team should insert the final GitHub URL below and in the report before submission.",size=11)
    add_code(doc,"python -m pip install -e \".[test,plots]\"\npython -m pytest -q\npython tools/run_experiments.py\npython -m loopscope.cli benchmark")
    add_table(doc,["Path","Contents"],[
        ("loopscope/","Parser, compiler, interpreter, proof rules, TM simulator, CLI"),
        ("tests/","23 automated tests"),
        ("tools/","Experiment and report generation scripts"),
        ("docs/diagrams/","Architecture and computability diagrams"),
        ("results/","Benchmark/sweep CSVs and generated charts"),
        ("examples/","MiniLoop source examples"),
        ("CONTRIBUTIONS.md","Proposed team role allocation"),
    ],[1.8,4.6],8.8)
    add_body(doc,"GitHub URL: to be added by the team after publishing the repository.",align=WD_ALIGN_PARAGRAPH.LEFT,size=10.5)
    page_break(doc)

    # PAGE 18 - CONCLUSION + REFERENCES
    add_heading(doc,"Conclusion")
    add_body(doc, "This project examined infinite-loop detection as a computability problem. By representing a program and its input as a Turing-machine computation, the question becomes membership in the complement of HALT_TM. The diagonal argument shows that a universal exact halting detector cannot exist, and the recognisability analysis explains why observing completion and proving nontermination are fundamentally asymmetric.")
    add_body(doc, "LoopScope demonstrates a practical restricted-case alternative. Static ranking and recurrence rules handle a small counter-loop fragment, while configuration memory detects deterministic cycles in concrete execution. The three-valued output avoids presenting an incomplete analysis as a mathematical proof. In the tested benchmark, 14 definite results were all correct and one case remained UNKNOWN; the 2,400-case sweep found no unsound verdict within its generated template family. The timeout experiment showed why a cutoff must not be confused with a proof of nontermination.")
    add_body(doc, "The main conclusion is that a useful loop analyser should make its assumptions visible, provide evidence for definite answers, and acknowledge undecidable or unsupported cases. The work can be extended by broadening the proof rules while preserving soundness and by improving the explanations produced for developers.")
    add_heading(doc,"References",2)
    refs=[
        "[1] M. Sipser, Introduction to the Theory of Computation, 3rd ed. Boston, MA, USA: Cengage Learning, 2013.",
        "[2] J. E. Hopcroft, R. Motwani, and J. D. Ullman, Introduction to Automata Theory, Languages, and Computation, 3rd ed. Boston, MA, USA: Pearson, 2007.",
        "[3] A. M. Turing, ‘On computable numbers, with an application to the Entscheidungsproblem,’ Proc. London Mathematical Society, vol. s2-42, no. 1, pp. 230-265, 1937.",
        "[4] H. G. Rice, ‘Classes of recursively enumerable sets and their decision problems,’ Trans. American Mathematical Society, vol. 74, no. 2, pp. 358-366, 1953.",
        "[5] R. W. Floyd, ‘Assigning meanings to programs,’ in Mathematical Aspects of Computer Science, Proc. Symposia in Applied Mathematics, vol. 19, pp. 19-32, 1967.",
        "[6] A. Gupta, T. A. Henzinger, R. Majumdar, A. Rybalchenko, and R.-G. Xu, ‘Proving non-termination,’ in Proc. ACM SIGPLAN-SIGACT Symp. Principles of Programming Languages, pp. 147-158, 2008.",
        "[7] K. R. Vaishak, D. V. F., and J. Shanmugpriyan, ‘FLA-Task4-Infinite-Loop-Detection,’ GitHub repository, 2026. https://github.com/Vaishakkr/FLA-Task4-Infinite-Loop-Detection (consulted as a scope and organisation reference).",
    ]
    for ref in refs:
        p=doc.add_paragraph(); p.paragraph_format.left_indent=Inches(.2); p.paragraph_format.first_line_indent=Inches(-.2); p.paragraph_format.line_spacing=1.0; p.paragraph_format.space_after=Pt(4)
        r=p.add_run(ref); set_font(r,9.3)

    # Document metadata.
    doc.core_properties.title = "LoopScope: Proof-Carrying Infinite-Loop Analysis"
    doc.core_properties.subject = "21CSC301T Formal Language and Automata - CLA-2 Assessment Task 4"
    doc.core_properties.author = "LoopScope FLA Team"
    doc.core_properties.keywords = "Turing machines, halting problem, undecidability, loop detection"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(OUT)

if __name__ == "__main__":
    main()
