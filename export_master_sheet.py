import json
import os

files = [
    ("MTH 101", "data/mth_101.json"),
    ("PHY 101", "data/phy_101.json"),
    ("CHM 101", "data/chm_101.json")
]

html_out = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>BAES Mock CBT - Master Question Reference Sheet</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    window.MathJax = {
      tex: { inlineMath: [['\\\\(', '\\\\)'], ['$', '$']] }
    };
  </script>
  <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
  <style>
    @media print {
      .page-break { page-break-after: always; }
      body { font-size: 11pt; }
    }
  </style>
</head>
<body class="bg-gray-100 text-gray-900 p-8">
  <div class="max-w-4xl mx-auto bg-white p-8 rounded-xl shadow border border-gray-200">
    <div class="border-b pb-4 mb-6 text-center">
      <h1 class="text-2xl font-bold text-blue-900">BAES MOCK CBT - MASTER QUESTION DIRECTORY</h1>
      <p class="text-sm text-gray-600 mt-1">Official Invigilator & Course Rep Verification Reference</p>
    </div>
"""

for course, path in files:
    if not os.path.exists(path):
        continue
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    html_out += f"""
    <div class="mt-8 page-break">
      <h2 class="text-xl font-bold bg-blue-100 text-blue-900 px-4 py-2 rounded mb-4">{course} ({len(data)} Questions)</h2>
      <div class="space-y-6">
    """

    for idx, q in enumerate(data, 1):
        q_text = q.get("question", "")
        options = q.get("options", [])
        correct = q.get("answer_index", 0)

        html_out += f"""
        <div class="p-4 border rounded-lg bg-gray-50 border-gray-200">
          <p class="font-semibold text-gray-800">Q{idx}. {q_text}</p>
          <div class="grid grid-cols-2 gap-2 mt-2 text-sm">
        """
        labels = ["A", "B", "C", "D"]
        for o_idx, opt in enumerate(options):
            is_correct = "text-green-700 font-bold" if o_idx == correct else "text-gray-700"
            star = " (✓)" if o_idx == correct else ""
            lbl = labels[o_idx] if o_idx < len(labels) else str(o_idx)
            html_out += f"""<div class="{is_correct}">{lbl}. {opt}{star}</div>"""

        html_out += """
          </div>
        </div>
        """
    html_out += "</div></div>"

html_out += """
  </div>
</body>
</html>
"""

with open("master_questions_sheet.html", "w", encoding="utf-8") as f:
    f.write(html_out)

print("[SUCCESS] Created 'master_questions_sheet.html'! Double click to open in browser and print to PDF or share with course reps.")