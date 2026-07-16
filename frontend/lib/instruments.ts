/** The household asset classes NextRupee reasons about. Each maps to an authored
 *  corpus doc (grounded answers) and a question that routes there through the guarded
 *  /api/ask. Reused by the AskBox explorer and, later, the allocation split. */

export type InstrumentKind =
  | "cash"
  | "fd"
  | "bonds"
  | "smallsavings"
  | "equity"
  | "index"
  | "gold"
  | "commodities"
  | "realestate";

export interface Instrument {
  kind: InstrumentKind;
  label: string;
  question: string;
}

export const INSTRUMENTS: Instrument[] = [
  { kind: "cash", label: "Cash & liquid", question: "How do liquid funds and savings accounts work?" },
  { kind: "fd", label: "Fixed deposits", question: "How do fixed deposits work, and when do they make sense?" },
  { kind: "bonds", label: "Bonds", question: "What are bonds and how risky are they?" },
  { kind: "smallsavings", label: "PPF / EPF", question: "How do PPF and EPF compare for long-term saving?" },
  { kind: "equity", label: "Shares", question: "How does the share market actually work?" },
  { kind: "index", label: "Index funds", question: "What is an index fund and why are they popular?" },
  { kind: "gold", label: "Gold", question: "How much gold should I hold in my plan?" },
  { kind: "commodities", label: "Commodities", question: "Should I invest in silver or other commodities?" },
  { kind: "realestate", label: "Real estate", question: "Is real estate a good investment for me?" },
];
