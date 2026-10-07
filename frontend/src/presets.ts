// Examples deliberately use small label sets so the question token budget stays useful.
import type { Prediction } from "./types";
export const presets: Record<string, Prediction> = {
  "Support triage": {
    state:
      "Hi, we were billed twice for March. Please refund the duplicate today or we will cancel our plan.",
    questions: {
      department: {
        type: "choice",
        instructions: "Which department should handle this request?",
        criteria: {
          billing: "invoices, payments, refunds",
          technical: "bugs, outages, system errors",
          other: "everything else",
        },
      },
      urgency: {
        type: "score",
        instructions: "How urgent is this request?",
        criteria: ["not urgent", "soon", "blocking or critical deadline"],
      },
      churn_risk: {
        type: "noul",
        instructions: "Does the user threaten to cancel or leave?",
      },
    },
  },
  "French support": {
    state:
      "J’ai été facturé deux fois. Merci de rembourser le paiement en double.",
    questions: {
      department: {
        type: "choice",
        instructions: "Which department should handle this?",
        criteria: {
          billing: "invoices, payments and refunds",
          technical: "bugs and outages",
          other: "anything else",
        },
      },
    },
  },
  "Arabic support": {
    state: "تم خصم المبلغ مرتين من حسابي. أرجو إعادة المبلغ الزائد.",
    questions: {
      department: {
        type: "choice",
        instructions: "Which department should handle this request?",
        criteria: {
          billing: "invoices, payments, refunds",
          technical: "bugs, outages, system errors",
          other: "everything else",
        },
      },
    },
  },
  "Invoice decision": {
    model: "typed-decisions",
    state: {
      invoice_id: "INV-4411",
      amount: 250,
      currency: "USD",
      purchase_order: "PO-2026-91",
      due_date: "2026-10-15",
      status: "approved",
    },
    questions: {
      next_step: {
        type: "choice",
        instructions: "What should happen to this invoice?",
        criteria: {
          pay: "approved and complete invoice ready for payment",
          review: "invoice needs review or clarification",
          reject: "invalid invoice",
        },
      },
    },
  },
  "Sentiment choice": {
    state:
      "The support team solved my problem quickly. I am very happy with the service.",
    questions: {
      sentiment: {
        type: "choice",
        instructions: "Is the review positive or negative?",
        criteria: { A: "the review is positive", B: "the review is negative" },
      },
    },
  },
};
