import json
import os
import re
import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# ==========================================
# 1. EXACT OVERRIDES BY 1-BASED QUESTION NUMBER
# ==========================================
MTH_INDEX_PATCHES = {
    9: {
        "question": "Which of the following numbers is irrational?",
        "options": ["3.14", "\\(\\sqrt{16}\\)", "\\(\\frac{22}{7}\\)", "\\(\\sqrt{2}\\)"],
        "answer_index": 3
    },
    15: {
        "question": "The multiplicative inverse of \\(\\sqrt{3}\\) is:",
        "options": ["\\(-\\sqrt{3}\\)", "\\(\\frac{1}{3}\\)", "\\(\\frac{1}{\\sqrt{3}}\\)", "1"],
        "answer_index": 2
    },
    16: {
        "question": "The sum of the first \\(n\\) natural numbers is given by:",
        "options": ["\\(n(n+1)\\)", "\\(\\frac{n(n+1)}{2}\\)", "\\(n^2\\)", "\\(\\frac{n(n-1)}{2}\\)"],
        "answer_index": 1
    },
    22: {
        "question": "If \\(\\alpha\\) and \\(\\beta\\) are roots of \\(ax^2 + bx + c = 0\\), then \\(\\alpha + \\beta =\\)",
        "options": ["\\(\\frac{b}{a}\\)", "\\(-\\frac{b}{a}\\)", "\\(\\frac{c}{a}\\)", "\\(-\\frac{c}{a}\\)"],
        "answer_index": 1
    },
    33: {
        "question": "De Moivre's Theorem states that \\((\\cos\\theta + i\\sin\\theta)^n =\\)",
        "options": [
            "\\(\\cos(n\\theta) - i\\sin(n\\theta)\\)",
            "\\(n(\\cos\\theta + i\\sin\\theta)\\)",
            "\\(\\cos(n\\theta) + i\\sin(n\\theta)\\)",
            "\\(\\cos^n\\theta + i\\sin^n\\theta\\)"
        ],
        "answer_index": 2
    },
    34: {
        "question": "Convert the complex number \\(z = 1 + \\sqrt{3}i\\) to polar form.",
        "options": [
            "\\(2\\left(\\cos\\frac{\\pi}{6} + i\\sin\\frac{\\pi}{6}\\right)\\)",
            "\\(2\\left(\\cos\\frac{\\pi}{3} + i\\sin\\frac{\\pi}{3}\\right)\\)",
            "\\(\\sqrt{2}\\left(\\cos\\frac{\\pi}{3} + i\\sin\\frac{\\pi}{3}\\right)\\)",
            "\\(2\\left(\\cos\\frac{\\pi}{4} + i\\sin\\frac{\\pi}{4}\\right)\\)"
        ],
        "answer_index": 1
    },
    37: {
        "question": "Which of the following represents the argument of \\(z = 1 + i\\)?",
        "options": ["\\(\\frac{\\pi}{2}\\)", "\\(\\frac{\\pi}{3}\\)", "\\(\\frac{\\pi}{4}\\)", "\\(\\pi\\)"],
        "answer_index": 2
    },
    38: {
        "question": "Convert \\(180^\\circ\\) to radians.",
        "options": ["\\(\\frac{\\pi}{2}\\)", "\\(\\pi\\)", "\\(2\\pi\\)", "\\(\\frac{3\\pi}{2}\\)"],
        "answer_index": 1
    },
    39: {
        "question": "The arc length \\(s\\) of a circle of radius \\(r\\) subtending an angle \\(\\theta\\) in radians is:",
        "options": ["\\(s = \\frac{1}{2}r^2\\theta\\)", "\\(s = r\\theta\\)", "\\(s = \\pi r^2 \\theta\\)", "\\(s = \\frac{\\theta}{r}\\)"],
        "answer_index": 1
    },
    40: {
        "question": "What is the exact value of \\(\\sin(30^\\circ)\\)?",
        "options": ["\\(\\frac{\\sqrt{3}}{2}\\)", "\\(\\frac{1}{2}\\)", "\\(\\frac{\\sqrt{2}}{2}\\)", "1"],
        "answer_index": 1
    },
    42: {
        "question": "The Pythagorean identity states that:",
        "options": ["\\(\\sin^2\\theta - \\cos^2\\theta = 1\\)", "\\(\\sin^2\\theta + \\cos^2\\theta = 0\\)", "\\(\\tan^2\\theta = 1\\)", "\\(\\sin^2\\theta + \\cos^2\\theta = 1\\)"],
        "answer_index": 3
    },
    44: {
        "question": "Using the double angle formula, \\(\\cos(2\\theta)\\) is equivalent to:",
        "options": ["\\(2\\sin\\theta\\cos\\theta\\)", "\\(\\cos^2\\theta - \\sin^2\\theta\\)", "\\(1 - 2\\cos^2\\theta\\)", "\\(2\\sin^2\\theta - 1\\)"],
        "answer_index": 1
    },
    46: {
        "question": "Calculate the principal argument of \\(-1 - i\\).",
        "options": ["\\(\\frac{\\pi}{4}\\)", "\\(-\\frac{3\\pi}{4}\\)", "\\(\\frac{3\\pi}{4}\\)", "\\(-\\frac{\\pi}{4}\\)"],
        "answer_index": 1
    },
    47: {
        "question": "If \\(z = r(\\cos\\theta + i\\sin\\theta)\\), then \\(z^{-1}\\) is:",
        "options": [
            "\\(r(\\cos\\theta - i\\sin\\theta)\\)",
            "\\(\\frac{1}{r}(\\cos\\theta + i\\sin\\theta)\\)",
            "\\(\\frac{1}{r}(\\cos\\theta - i\\sin\\theta)\\)",
            "\\(-r(\\cos\\theta + i\\sin\\theta)\\)"
        ],
        "answer_index": 2
    },
    48: {
        "question": "Evaluate \\(\\sec^2\\theta - \\tan^2\\theta\\).",
        "options": ["0", "-1", "1", "\\(\\csc^2\\theta\\)"],
        "answer_index": 2
    },
    49: {
        "question": "What is the area of a circular sector of radius 4 cm subtending an angle of \\(\\frac{\\pi}{2}\\) radians?",
        "options": ["\\(4\\pi\\text{ cm}^2\\)", "\\(2\\pi\\text{ cm}^2\\)", "\\(8\\pi\\text{ cm}^2\\)", "\\(16\\pi\\text{ cm}^2\\)"],
        "answer_index": 0
    },
    50: {
        "question": "The value of \\(\\cos(90^\\circ + \\theta)\\) is equal to:",
        "options": ["\\(\\sin\\theta\\)", "\\(-\\sin\\theta\\)", "\\(\\cos\\theta\\)", "\\(-\\cos\\theta\\)"],
        "answer_index": 1
    },
    51: {
        "question": "Let \\(S_n\\) be the sum of a geometric series. As \\(n \\rightarrow \\infty\\), if \\(|r| < 1\\), \\(S_n \\rightarrow\\)",
        "options": ["\\(\\frac{a}{1-r}\\)", "\\(\\infty\\)", "0", "\\(\\frac{a}{r-1}\\)"],
        "answer_index": 0
    },
    58: {
        "question": "The binomial coefficient \\(\\binom{n}{r}\\) is computed as:",
        "options": ["\\(\\frac{n!}{r!(n-r)!}\\)", "\\(\\frac{n!}{(n-r)!}\\)", "\\(\\frac{n!}{r!}\\)", "\\(n!\\)"],
        "answer_index": 0
    },
    59: {
        "question": "Evaluate \\(\\binom{5}{2}\\).",
        "options": ["5", "10", "20", "120"],
        "answer_index": 1
    },
    62: {
        "question": "Convert the complex number \\(z = 1 + \\sqrt{3}i\\) to polar form.",
        "options": [
            "\\(2\\left(\\cos\\frac{\\pi}{6} + i\\sin\\frac{\\pi}{6}\\right)\\)",
            "\\(2\\left(\\cos\\frac{\\pi}{3} + i\\sin\\frac{\\pi}{3}\\right)\\)",
            "\\(\\sqrt{2}\\left(\\cos\\frac{\\pi}{3} + i\\sin\\frac{\\pi}{3}\\right)\\)",
            "\\(2\\left(\\cos\\frac{\\pi}{4} + i\\sin\\frac{\\pi}{4}\\right)\\)"
        ],
        "answer_index": 1
    },
    65: {
        "question": "If \\(\\sin\\theta = \\frac{3}{5}\\) and \\(\\theta\\) is acute, \\(\\cos\\theta =\\)",
        "options": ["\\(\\frac{5}{4}\\)", "\\(\\frac{4}{5}\\)", "\\(\\frac{3}{4}\\)", "\\(\\frac{4}{3}\\)"],
        "answer_index": 1
    },
    66: {
        "question": "What is the period of the function \\(y = \\sin x\\)?",
        "options": ["\\(\\pi\\)", "\\(2\\pi\\)", "\\(\\frac{\\pi}{2}\\)", "360"],
        "answer_index": 1
    },
    73: {
        "question": "Simplify \\(\\frac{1}{i}\\).",
        "options": ["\\(i\\)", "\\(-i\\)", "1", "-1"],
        "answer_index": 1
    },
    77: {
        "question": "Find \\(\\tan(A - B)\\) if it expands to:",
        "options": [
            "\\(\\frac{\\tan A + \\tan B}{1 - \\tan A \\tan B}\\)",
            "\\(\\frac{\\tan A - \\tan B}{1 + \\tan A \\tan B}\\)",
            "\\(\\frac{\\tan A - \\tan B}{1 - \\tan A \\tan B}\\)",
            "\\(\\tan A - \\tan B\\)"
        ],
        "answer_index": 1
    },
    78: {
        "question": "The identity \\(\\cos(2\\theta) = \\cos^2\\theta - \\sin^2\\theta\\) is derived from:",
        "options": ["Pythagorean theorem", "Addition formula", "De Moivre's theorem only", "Factor formula"],
        "answer_index": 1
    },
    83: {
        "question": "The rational number \\(\\frac{1}{3}\\) in decimal form is:",
        "options": ["Terminating", "Non-terminating and non-repeating", "Non-terminating and repeating", "Irrational"],
        "answer_index": 2
    },
    87: {
        "question": "Write \\(\\frac{1}{1+i}\\) in standard form \\(a + bi\\).",
        "options": ["\\(\\frac{1}{2} - \\frac{1}{2}i\\)", "\\(\\frac{1}{2} + \\frac{1}{2}i\\)", "\\(1 - i\\)", "\\(-1 + i\\)"],
        "answer_index": 0
    },
    91: {
        "question": "If \\(\\sin\\theta = \\cos\\theta\\) and \\(0 < \\theta < \\frac{\\pi}{2}\\), then \\(\\theta =\\)",
        "options": ["\\(\\frac{\\pi}{6}\\)", "\\(\\frac{\\pi}{4}\\)", "\\(\\frac{\\pi}{3}\\)", "\\(\\frac{\\pi}{2}\\)"],
        "answer_index": 1
    },
    92: {
        "question": "The identity for \\(\\sin(2\\theta)\\) is:",
        "options": ["\\(2\\sin\\theta\\cos\\theta\\)", "\\(\\cos^2\\theta - \\sin^2\\theta\\)", "\\(\\sin\\theta + \\cos\\theta\\)", "\\(1 - 2\\sin^2\\theta\\)"],
        "answer_index": 0
    },
    93: {
        "question": "Express \\(120^\\circ\\) in radians.",
        "options": ["\\(\\frac{2\\pi}{3}\\)", "\\(\\frac{3\\pi}{4}\\)", "\\(\\frac{\\pi}{2}\\)", "\\(\\frac{5\\pi}{6}\\)"],
        "answer_index": 0
    },
    95: {
        "question": "Find the general solution for \\(\\sin\\theta = 0\\).",
        "options": ["\\(\\theta = 2n\\pi\\)", "\\(\\theta = n\\pi\\)", "\\(\\theta = \\frac{\\pi}{2} + n\\pi\\)", "\\(\\theta = n\\pi + \\frac{\\pi}{4}\\)"],
        "answer_index": 1
    },
    96: {
        "question": "Which of these is the correct formula for \\(\\cos A + \\cos B\\)?",
        "options": [
            "\\(2\\sin\\left(\\frac{A+B}{2}\\right)\\cos\\left(\\frac{A-B}{2}\\right)\\)",
            "\\(2\\cos\\left(\\frac{A+B}{2}\\right)\\cos\\left(\\frac{A-B}{2}\\right)\\)",
            "\\(-2\\sin\\left(\\frac{A+B}{2}\\right)\\sin\\left(\\frac{A-B}{2}\\right)\\)",
            "\\(2\\cos\\left(\\frac{A+B}{2}\\right)\\sin\\left(\\frac{A-B}{2}\\right)\\)"
        ],
        "answer_index": 1
    },
    100: {
        "question": "Evaluate \\(\\cos(60^\\circ)\\).",
        "options": ["1", "\\(\\frac{\\sqrt{3}}{2}\\)", "\\(\\frac{1}{2}\\)", "0"],
        "answer_index": 2
    }
}

# ==========================================
# 2. EXACT OVERRIDES FOR GLITCHED CHM / PHY PROMPTS
# ==========================================
CHM_INDEX_PATCHES = {
    8: {
        "question": "What type of reaction is represented by \\(\\text{CuCl}_2(aq) + 2\\text{AgNO}_3(aq) \\rightarrow \\text{Cu(NO}_3)_2(aq) + 2\\text{AgCl}(s)\\)?"
    },
    12: {
        "question": "In the reaction \\(\\text{Fe}_2\\text{O}_3 + 3\\text{CO} \\rightarrow 2\\text{Fe} + 3\\text{CO}_2\\), what process does \\(\\text{Fe}_2\\text{O}_3\\) undergo?"
    },
    19: {
        "question": "In the reaction \\(\\text{H}_2\\text{O}_2(aq) + \\text{Cl}_2(g) + 2\\text{OH}^-(aq) \\rightarrow 2\\text{H}_2\\text{O} + 2\\text{Cl}^-(aq) + \\text{O}_2(g)\\), what is the role of hydrogen peroxide?"
    },
    25: {
        "question": "For the combustion of octane: \\(2\\text{C}_8\\text{H}_{18}(l) + 25\\text{O}_2(g) \\rightarrow 16\\text{CO}_2(g) + 18\\text{H}_2\\text{O}(g)\\), how many moles of \\(\\text{CO}_2\\) form when 22.0 moles of \\(\\text{C}_8\\text{H}_{18}\\) burn?"
    },
    27: {
        "question": "For the reaction \\(aA(aq) + bB(aq) \\rightleftharpoons cC(aq) + dD(aq)\\), what is the correct expression for \\(K_c\\)?"
    },
    29: {
        "question": "If \\(\\Delta n > 0\\) for a gaseous reaction, which of the following is true?"
    },
    57: {
        "question": "What is the standard free energy change \\(\\Delta G^\\circ\\) for a cell related to the standard cell potential \\(E^\\circ_{\\text{cell}}\\)?"
    },
    73: {
        "question": "For a second order reaction \\(A + A \\rightarrow P\\), the integrated rate law is:"
    },
    79: {
        "question": "For a sparingly soluble salt \\(\\text{AgCl}(s) \\rightleftharpoons \\text{Ag}^+(aq) + \\text{Cl}^-(aq)\\), the solubility product \\(K_{sp}\\) is expressed as:"
    }
}

PHY_INDEX_PATCHES = {
    73: {
        "question": "If work \\(W\\) is positive, the angle \\(\\theta\\) between the force and displacement is:"
    },
    91: {
        "question": "If vector \\(A = A_x\\hat{i} + A_y\\hat{j}\\), the angle \\(\\theta\\) it makes with the x-axis is found using:"
    },
    93: {
        "question": "A particle moves such that its displacement is \\(x = ut + \\frac{1}{2}at^2\\). If \\(u = 0\\) and \\(a = 2\\text{ m/s}^2\\), the displacement at \\(t = 5\\text{ s}\\) is:"
    }
}

def apply_patches():
    # 1. Patch MTH 101
    mth_file = "data/mth_101.json"
    with open(mth_file, "r", encoding="utf-8") as f:
        mth_data = json.load(f)

    for q_num, patch in MTH_INDEX_PATCHES.items():
        idx = q_num - 1
        if 0 <= idx < len(mth_data):
            for k, v in patch.items():
                mth_data[idx][k] = v

    with open(mth_file, "w", encoding="utf-8") as f:
        json.dump(mth_data, f, indent=2, ensure_ascii=False)
    print(f"[OK] MTH 101: Patched {len(MTH_INDEX_PATCHES)} specific questions by direct index.")

    # 2. Patch CHM 101
    chm_file = "data/chm_101.json"
    with open(chm_file, "r", encoding="utf-8") as f:
        chm_data = json.load(f)

    for q_num, patch in CHM_INDEX_PATCHES.items():
        idx = q_num - 1
        if 0 <= idx < len(chm_data):
            for k, v in patch.items():
                chm_data[idx][k] = v

    with open(chm_file, "w", encoding="utf-8") as f:
        json.dump(chm_data, f, indent=2, ensure_ascii=False)
    print(f"[OK] CHM 101: Patched {len(CHM_INDEX_PATCHES)} questions by direct index.")

    # 3. Patch PHY 101
    phy_file = "data/phy_101.json"
    with open(phy_file, "r", encoding="utf-8") as f:
        phy_data = json.load(f)

    for q_num, patch in PHY_INDEX_PATCHES.items():
        idx = q_num - 1
        if 0 <= idx < len(phy_data):
            for k, v in patch.items():
                phy_data[idx][k] = v

    with open(phy_file, "w", encoding="utf-8") as f:
        json.dump(phy_data, f, indent=2, ensure_ascii=False)
    print(f"[OK] PHY 101: Patched {len(PHY_INDEX_PATCHES)} questions by direct index.")

    # 4. Commit all clean questions to Firestore
    all_qs = mth_data + chm_data + phy_data
    print(f"\nPushing all {len(all_qs)} finalized questions to Firestore...")
    batch = db.batch()
    count = 0
    for q in all_qs:
        doc_ref = db.collection("questions").document(str(q.get("id")))
        batch.set(doc_ref, q, merge=True)
        count += 1
        if count % 400 == 0:
            batch.commit()
            batch = db.batch()
    batch.commit()
    print("[SUCCESS] All targeted fixes applied to JSON and committed to Firestore!")

if __name__ == "__main__":
    apply_patches()