import pandas as pd
import os
import ollama
import json
import re
from pathlib import Path
from typing import Any, Dict, List

OLLAMA_HOST = os.getenv(
    "OLLAMA_HOST",
    "http://localhost:11434"
)

ollama_client = ollama.Client(host=OLLAMA_HOST)

class FinancialAnalyzer:
    """A Mutual Fund Advisor bot that parses a client's Excel portfolio and answers queries using Ollama."""

    def __init__(self, excel_path: str | Path):
        self.excel_path = Path(excel_path)
        if not self.excel_path.exists():
            raise FileNotFoundError(f"Excel file not found at: {self.excel_path}")
        
        # Parse the entire Excel workbook
        self.portfolio_data = self._parse_workbook()
        self.portfolio_summary_markdown = self._generate_markdown_summary()

    def _clean_val(self, val: Any) -> Any:
        if pd.isna(val):
            return None
        if isinstance(val, (int, float)):
            return round(val, 2)
        return str(val).strip()

    def _parse_workbook(self) -> Dict[str, Any]:
        xl = pd.ExcelFile(self.excel_path)
        data = {}

        # 1. Parse Holder Wise summary
        if 'Holder Wise' in xl.sheet_names:
            df = xl.parse('Holder Wise', header=None)
            if len(df) > 2:
                headers = [str(x).strip() for x in df.iloc[1].tolist()]
                holders = []
                for idx in range(2, len(df)):
                    row = df.iloc[idx].tolist()
                    if pd.isna(row[0]):
                        continue
                    holder_info = {headers[i]: self._clean_val(row[i]) for i in range(len(headers)) if i < len(row)}
                    holders.append(holder_info)
                data['holders'] = holders

        # 2. Parse Active Sip
        if 'Active Sip' in xl.sheet_names:
            df = xl.parse('Active Sip', header=None)
            if len(df) > 2:
                headers = [str(x).strip() for x in df.iloc[1].tolist()]
                sips = []
                for idx in range(2, len(df)):
                    row = df.iloc[idx].tolist()
                    if pd.isna(row[0]) or str(row[0]).lower() == 'total':
                        continue
                    sip_info = {headers[i]: self._clean_val(row[i]) for i in range(len(headers)) if i < len(row)}
                    sips.append(sip_info)
                data['active_sips'] = sips

        # 3. Parse Folio Wise details (where detailed schemes are listed for each holder)
        if 'Folio Wise' in xl.sheet_names:
            df = xl.parse('Folio Wise', header=None)
            current_holder = None
            headers = None
            schemes = {}
            
            # Extract known holders for comparison
            known_holders = []
            if 'holders' in data:
                known_holders = [" ".join(h.get('Holder Name', '').lower().split()) for h in data['holders'] if h.get('Holder Name')]
            
            for idx, row in df.iterrows():
                row_vals = list(row.values)
                non_na_vals = [x for x in row_vals if not pd.isna(x)]
                if len(non_na_vals) == 0:
                    continue
                
                # Check if this row lists a family member/holder name
                if len(non_na_vals) == 1:
                    val_str = str(non_na_vals[0]).strip()
                    val_norm = " ".join(val_str.lower().split())
                    
                    is_holder = False
                    if known_holders:
                        is_holder = val_norm in known_holders or any(val_norm in kh or kh in val_norm for kh in known_holders)
                    else:
                        is_holder = "valuation report" not in val_norm and "portfolio status" not in val_norm and "period" not in val_norm
                        
                    if is_holder:
                        current_holder = val_str
                        if 'holders' in data:
                            for h in data['holders']:
                                h_name = h.get('Holder Name')
                                if h_name and " ".join(h_name.lower().split()) == val_norm:
                                    current_holder = h_name
                                    break
                        schemes[current_holder] = []
                        headers = None
                        continue
                
                # Column headers row
                if 'Scheme Name' in row_vals:
                    headers = [str(x).strip() for x in row_vals]
                    continue
                    
                if current_holder and headers:
                    if str(row_vals[0]).lower() == 'total':
                        continue
                    scheme_info = {}
                    for i, val in enumerate(row_vals):
                        if i < len(headers):
                            h = headers[i]
                            if pd.isna(h):
                                continue
                            scheme_info[h] = self._clean_val(val)
                    if scheme_info.get('Scheme Name'):
                        schemes[current_holder].append(scheme_info)
            data['portfolio_schemes'] = schemes

        # 4. Parse Category Wise
        if 'Category Wise' in xl.sheet_names:
            df = xl.parse('Category Wise', header=None)
            if len(df) > 2:
                headers = [str(x).strip() for x in df.iloc[1].tolist()]
                categories = []
                for idx in range(2, len(df)):
                    row = df.iloc[idx].tolist()
                    if pd.isna(row[0]):
                        continue
                    cat_info = {headers[i]: self._clean_val(row[i]) for i in range(len(headers)) if i < len(row)}
                    categories.append(cat_info)
                data['categories'] = categories

        # 5. Parse AMC Wise
        if 'AMC Wise' in xl.sheet_names:
            df = xl.parse('AMC Wise', header=None)
            if len(df) > 2:
                headers = [str(x).strip() for x in df.iloc[1].tolist()]
                amcs = []
                for idx in range(2, len(df)):
                    row = df.iloc[idx].tolist()
                    if pd.isna(row[0]):
                        continue
                    amc_info = {headers[i]: self._clean_val(row[i]) for i in range(len(headers)) if i < len(row)}
                    amcs.append(amc_info)
                data['amc_wise'] = amcs

        return data

    def _generate_markdown_summary(self) -> str:
        """Create a detailed, context-rich Markdown representation of the parsed portfolio data."""
        lines = []
        lines.append("# MUTUAL FUND PORTFOLIO SUMMARY REPORT")
        
        # Holder Wise summary
        if 'holders' in self.portfolio_data:
            lines.append("\n## Holder Overview")
            for h in self.portfolio_data['holders']:
                lines.append(f"- **{h.get('Holder Name')}**: SIP: Rs.{h.get('SIP') or 0}, Current Value: Rs.{h.get('Current Value') or 0}, XIRR: {h.get('XIRR') or 0}%, ABS: {h.get('ABS') or 0}%")

        # Active SIPs
        if 'active_sips' in self.portfolio_data:
            lines.append("\n## Active SIP Details")
            for s in self.portfolio_data['active_sips']:
                lines.append(f"- Holder: **{s.get('Holder Name')}** | Scheme: **{s.get('Scheme Name')}** | SIP Amount: Rs.{s.get('Amount')} | Frequency: {s.get('Frequency')} | Date: {s.get('Sip Date')}")

        # Categories
        if 'categories' in self.portfolio_data:
            lines.append("\n## Asset Allocation by Category")
            for c in self.portfolio_data['categories']:
                lines.append(f"- **{c.get('Category Name')}**: Cost: Rs.{c.get('Cost of Investment') or 0}, Current Value: Rs.{c.get('Current Value') or 0}, XIRR: {c.get('XIRR') or 0}%")

        # Portfolio schemes detailed
        if 'portfolio_schemes' in self.portfolio_data:
            lines.append("\n## Detailed Schemes by Holder")
            for holder, schemes in self.portfolio_data['portfolio_schemes'].items():
                lines.append(f"\n### Holder: {holder}")
                for s in schemes:
                    lines.append(
                        f"- Scheme: **{s.get('Scheme Name')}**\n"
                        f"  - Folio No: {s.get('Folio No')}\n"
                        f"  - Cost of Investment: Rs.{s.get('Cost of Investment') or 0}\n"
                        f"  - Current Value: Rs.{s.get('Current value') or 0}\n"
                        f"  - Units: {s.get('Units')}\n"
                        f"  - Cost NAV (Avg NAV): Rs.{s.get('Avg NAV') or 0}\n"
                        f"  - Current NAV: Rs.{s.get('Current NAV') or 0}\n"
                        f"  - Notional P/L: Rs.{s.get('Notional P/L') or 0}\n"
                        f"  - Booked P/L: Rs.{s.get('Booked P/L') or 0}\n"
                        f"  - XIRR: {s.get('XIRR') or 0}%\n"
                        f"  - Nominee: {s.get('Nominee') or 'Not specified'}"
                    )
        
        return "\n".join(lines)

    def _generate_compact_summary(self) -> str:
        """Create a compact summary for the LLM system prompt to reduce token count and speed up responses."""
        lines = []
        lines.append("PORTFOLIO DATA:")

        # Holder summary (compact)
        if 'holders' in self.portfolio_data:
            lines.append("\nHOLDERS:")
            for h in self.portfolio_data['holders']:
                lines.append(f"  {h.get('Holder Name')}: SIP=Rs.{h.get('SIP') or 0}, Cost=Rs.{h.get('Cost of Investment') or 0}, Value=Rs.{h.get('Current Value') or 0}, XIRR={h.get('XIRR') or 0}%")

        # Active SIPs (compact)
        if 'active_sips' in self.portfolio_data:
            lines.append("\nACTIVE SIPs:")
            for s in self.portfolio_data['active_sips']:
                lines.append(f"  {s.get('Holder Name')} | {s.get('Scheme Name')} | Rs.{s.get('Amount')} | {s.get('Frequency')}")

        # Categories (compact)
        if 'categories' in self.portfolio_data:
            lines.append("\nCATEGORIES:")
            for c in self.portfolio_data['categories']:
                lines.append(f"  {c.get('Category Name')}: Cost=Rs.{c.get('Cost of Investment') or 0}, Value=Rs.{c.get('Current Value') or 0}, XIRR={c.get('XIRR') or 0}%")

        # Schemes (compact - one line per scheme)
        if 'portfolio_schemes' in self.portfolio_data:
            lines.append("\nSCHEMES:")
            for holder, schemes in self.portfolio_data['portfolio_schemes'].items():
                lines.append(f"  [{holder}]")
                for s in schemes:
                    lines.append(
                        f"    {s.get('Scheme Name')}: Cost=Rs.{s.get('Cost of Investment') or 0}, "
                        f"Value=Rs.{s.get('Current value') or 0}, XIRR={s.get('XIRR') or 0}%, "
                        f"Units={s.get('Units')}, Nominee={s.get('Nominee') or 'N/A'}"
                    )

        return "\n".join(lines)

    def _generate_compact_summary_for_holder(self, holder_name: str) -> str:
        """Create a compact summary filtered to a specific holder only."""
        lines = []
        lines.append(f"PORTFOLIO DATA FOR: {holder_name.upper()}")

        # Holder summary (only the matched holder)
        if 'holders' in self.portfolio_data:
            lines.append("\nHOLDER SUMMARY:")
            for h in self.portfolio_data['holders']:
                if holder_name.lower() in str(h.get('Holder Name', '')).lower():
                    lines.append(
                        f"  Name: {h.get('Holder Name')}\n"
                        f"  SIP=Rs.{h.get('SIP') or 0}, "
                        f"Cost=Rs.{h.get('Cost of Investment') or 0}, "
                        f"Current Value=Rs.{h.get('Current Value') or 0}, "
                        f"XIRR={h.get('XIRR') or 0}%, "
                        f"ABS={h.get('ABS') or 0}%"
                    )

        # Active SIPs (only for this holder)
        if 'active_sips' in self.portfolio_data:
            holder_sips = [
                s for s in self.portfolio_data['active_sips']
                if holder_name.lower() in str(s.get('Holder Name', '')).lower()
            ]
            if holder_sips:
                lines.append("\nACTIVE SIPs:")
                for s in holder_sips:
                    lines.append(
                        f"  {s.get('Scheme Name')} | Rs.{s.get('Amount')} | "
                        f"{s.get('Frequency')} | Date: {s.get('Sip Date')}"
                    )

        # Schemes (only for this holder)
        if 'portfolio_schemes' in self.portfolio_data:
            lines.append("\nSCHEMES:")
            for holder_key, schemes in self.portfolio_data['portfolio_schemes'].items():
                if holder_name.lower() in holder_key.lower():
                    for s in schemes:
                        lines.append(
                            f"  {s.get('Scheme Name')}: Cost=Rs.{s.get('Cost of Investment') or 0}, "
                            f"Value=Rs.{s.get('Current value') or 0}, XIRR={s.get('XIRR') or 0}%, "
                            f"Units={s.get('Units')}, Nominee={s.get('Nominee') or 'N/A'}"
                        )

        return "\n".join(lines)

    def answer_question(self, query: str) -> str:
        """Get advice or fact retrieval from Ollama (llama3) as a professional Mutual Fund Advisor."""
        # Use compact summary to reduce token count (~800 tokens instead of ~4000)
        compact_data = self._generate_compact_summary()

        holders_names = ", ".join([h.get('Holder Name') for h in self.portfolio_data.get('holders', []) if h.get('Holder Name')])
        system_prompt = (
            f"You are a Mutual Fund Advisor for clients {holders_names}.\n"
            f"{compact_data}\n\n"
            "Rules: Use exact figures from above data. Be concise. Address clients by name."
        )

        try:
            response = ollama_client.chat(
                model="llama3",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                options={"num_predict": 512}
            )
            return response["message"]["content"]
        except Exception as e:
            return f"Error contacting Ollama (llama3): {e}. Please make sure Ollama is running."
