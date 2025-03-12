# #!/bin/bash
# # Check Python availability
# if command -v python3 > /dev/null 2>&1; then
#    python_cmd="python3"
# elif command -v python > /dev/null 2>&1; then
#    python_cmd="python"
# else
#    echo "WARNING: Python3 is not installed. Commit review functionality will not work."
#    exit 1
# fi

# # Get the directory where this script is located
# SCRIPT_DIR="$(git config --global --get core.hookspath)"
# REPORTS_DIR="$SCRIPT_DIR/.commit-reports"

# # Create reports directory if it doesn't exist
# mkdir -p "$REPORTS_DIR"

# # Read the metadata file
# METADATA_FILE=".commit_metadata.json"

# if [ ! -f "$METADATA_FILE" ]; then
#     echo "No commit metadata found."
#     exit 0
# fi

# # # Display the results in HTML
# $python_cmd - "$METADATA_FILE" "$REPORTS_DIR" <<EOF
import json
import sys
import os
from datetime import datetime
import webbrowser

def create_html(metadata_file):
    try:
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
    except Exception as e:
        print(f"Error reading metadata file: {e}")
        return None

    # Get commit information
    commit_hash = os.popen('git rev-parse HEAD').read().strip()
    commit_msg = os.popen('git log -1 --pretty=%B').read().strip()
    commit_author = os.popen('git log -1 --pretty=%an').read().strip()
    commit_date = os.popen('git log -1 --pretty=%ad --date=local').read().strip()

    secrets_found = metadata.get('secrets_found', [])
    print(secrets_found)
    disallowed_files = metadata.get('disallowed_files', [])
    print(disallowed_files)
    secrets_table_rows = "".join(
        f"""<tr>
            <td class="sno">{i}</td>
            <td class="filename">{data.get('file', '')}</td>
            <td class="line-number">{data.get('line_number', '')}</td>
            <td class="secret"><div class="secret-content">{data.get('line', '')}</div></td>
        </tr>"""
        for i, data in enumerate(secrets_found, 1)
    ) if secrets_found else "<tr><td colspan='4' style='text-align: center;'>No secrets found</td></tr>"

    disallowed_files_rows = "".join(
        f"""<tr>
            <td class="sno">{i}</td>
            <td class="filename">{file}</td>
        </tr>"""
        for i, file in enumerate(disallowed_files, 1)
    ) if disallowed_files else "<tr><td colspan='2' style='text-align: center;'>No disallowed files</td></tr>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Commit Review Results</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.2.4/pdfmake.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.2.4/vfs_fonts.js"></script>
    <style>
        body {{ font-family: -apple-system, system-ui, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .commit-info {{ 
            background: #f8f9fa; 
            padding: 15px; 
            border-radius: 5px; 
            margin-bottom: 20px;
            border-left: 4px solid #07439C;
        }}
        .commit-info p {{ margin: 5px 0; }}
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin-top: 20px;
            table-layout: fixed;
        }}
        th, td {{ 
            padding: 12px; 
            text-align: left; 
            border: 1px solid #ddd;
            vertical-align: top;
            overflow-wrap: break-word;
        }}
        th {{ background: #07439C; color: white; }}
        tr:nth-child(even) {{ background: #f9f9f9; }}
        .secret-content {{ 
            color: #d32f2f; 
            font-family: monospace;
            white-space: pre-wrap;
            padding: 4px 8px;
            border-radius: 4px;
            background: rgba(211, 47, 47, 0.05);
        }}
        .line-number {{ color: #e74c3c; font-weight: bold; text-align: center; }}
        .sno {{ text-align: center; }}
        h1, h2 {{ color: #07439C; margin-bottom: 20px; }}
        .download-btn {{
            padding: 10px 20px;
            background-color: #07439C;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin-bottom: 20px;
        }}
        .download-btn:hover {{ background-color: #053278; }}
    </style>
</head>
<body>
    <div class="container">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h1>Commit Review Results</h1>
            <button id="downloadButton" class="download-btn">Download as PDF</button>
        </div>
        
        <div class="commit-info">
            <p><strong>Commit Hash:</strong> {commit_hash}</p>
            <p><strong>Author:</strong> {commit_author}</p>
            <p><strong>Date:</strong> {commit_date}</p>
            <p><strong>Message:</strong> {commit_msg}</p>
        </div>

        <h2>Disallowed Files:</h2>
        <table id="disallowedFilesTable">
            <tr>
                <th style="width:5%">S.No</th>
                <th style="width:95%">Filename</th>
            </tr>
            {disallowed_files_rows}
        </table>

        <h2>Potential Secrets:</h2>
        <table id="secretsTable">
            <tr>
                <th style="width:5%">S.No</th>
                <th style="width:25%">Filename</th>
                <th style="width:10%">Line #</th>
                <th style="width:60%">Secret</th>
            </tr>
            {secrets_table_rows}
        </table>
    </div>

    <script>
    document.getElementById("downloadButton").addEventListener("click", () => {
        // Get secrets table data
        const secretsTable = document.getElementById("secretsTable");
        const secretRows = secretsTable.querySelectorAll("tr:not(:first-child)");
        const secrets = Array.from(secretRows).map((row, index) => {
            const cells = row.querySelectorAll("td");
            return {
                sno: cells[0]?.innerText || "",
                filename: cells[1]?.innerText || "",
                lineNumber: cells[2]?.innerText || "",
                secret: cells[3]?.innerText || ""
            };
        });

        // Get disallowed files data if it exists
        const disallowedFilesTable = document.getElementById("disallowedFilesTable");
        const disallowedRows = disallowedFilesTable ? 
            Array.from(disallowedFilesTable.querySelectorAll("tr:not(:first-child)")) : [];
        const disallowedFiles = disallowedRows.map(row => {
            const cells = row.querySelectorAll("td");
            return {
                sno: cells[0]?.innerText || "",
                filename: cells[1]?.innerText || ""
            };
        });

        // Create file name using current date
        const currentDate = new Date();
        const formattedDate = currentDate.toLocaleDateString('en-GB', {
            day: '2-digit', month: 'short', year: 'numeric'
        }).replace(' ', '_').replace(',', '');
        const fileName = 'commit_review_' + formattedDate + '.pdf';

        // Create the PDF document definition
        const docDefinition = {
            pageOrientation: 'landscape',
            content: [
                { text: 'Commit Review Results', style: 'header' },
                // Disallowed Files Section
                ...(disallowedFiles.length ? [
                    { text: 'Disallowed Files Found:', style: 'subheader' },
                    {
                        table: {
                            headerRows: 1,
                            widths: ['5%', '95%'],
                            body: [
                                [
                                    { text: 'S.No', fillColor: '#E9E5E5', bold: true, alignment: 'center' },
                                    { text: 'Filename', fillColor: '#E9E5E5', bold: true }
                                ],
                                ...disallowedFiles.map(file => [
                                    { text: file.sno, alignment: 'center' },
                                    { text: file.filename }
                                ])
                            ]
                        },
                        margin: [0, 0, 0, 20]
                    }
                ] : []),
                // Secrets Section
                { text: 'Potential Secrets Found:', style: 'subheader' },
                {
                    table: {
                        headerRows: 1,
                        widths: ['5%', '25%', '10%', '60%'],
                        body: [
                            [
                                { text: 'S.No', fillColor: '#E9E5E5', bold: true, alignment: 'center' },
                                { text: 'Filename', fillColor: '#E9E5E5', bold: true },
                                { text: 'Line #', fillColor: '#E9E5E5', bold: true, alignment: 'center' },
                                { text: 'Secret', fillColor: '#E9E5E5', bold: true }
                            ],
                            ...secrets.map((secret, index) => [
                                { text: secret.sno, alignment: 'center' },
                                secret.filename,
                                { text: secret.lineNumber, alignment: 'center' },
                                secret.secret
                            ])
                        ]
                    }
                }
            ],
            styles: {
                header: {
                    fontSize: 18,
                    bold: true,
                    alignment: 'center',
                    margin: [0, 0, 0, 10]
                },
                subheader: {
                    fontSize: 14,
                    bold: true,
                    margin: [0, 10, 0, 5]
                }
            }
        };

        // Generate and download the PDF
        pdfMake.createPdf(docDefinition).download(fileName);
    });
    </script>
</body>
</html>"""

metadata_file = sys.argv[1]
reports_dir = sys.argv[2]

if os.path.exists(metadata_file):
    html_content = create_html(metadata_file)
    if html_content:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        html_report = os.path.join(reports_dir, f'commit_review_{timestamp}.html')
        with open(html_report, 'w') as f:
            f.write(html_content)
        webbrowser.open('file://' + os.path.abspath(html_report))
        print(f"\nCommit review report saved to: {html_report}")
        
        # Clean up old reports (keep last 5)
        reports = sorted([f for f in os.listdir(reports_dir) if f.startswith('commit_review_')], reverse=True)
        for old_report in reports[5:]:
            os.remove(os.path.join(reports_dir, old_report))


create_html("metadata.json")
# Clean up metadata file
# os.remove(metadata_file)


