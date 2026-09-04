import { Component } from '@angular/core'
import { RouterModule } from '@angular/router'
import { CommonModule } from '@angular/common'

interface AttackCard {
  id: string
  name: string
  category: string
  severity: 'Critical' | 'High' | 'Medium'
  channel: string
  description: string
  route: string | null
  implemented: boolean
}

@Component({
  selector: 'app-attack-hub',
  standalone: true,
  imports: [RouterModule, CommonModule],
  templateUrl: './attack-hub.component.html',
  styleUrls: ['./attack-hub.component.scss']
})
export class AttackHubComponent {
  attacks: AttackCard[] = [
    {
      id: 'ATK-001', name: 'Prompt Injection via Merchant Content', category: 'Agentic/LLM',
      severity: 'Critical', channel: 'Tool Output / Receipt',
      description: 'Malicious instructions hidden in merchant receipts or tool output.',
      route: '/agentic-banking', implemented: true
    },
    {
      id: 'ATK-002', name: 'Indirect Injection from Email/SMS', category: 'Agentic/LLM',
      severity: 'Critical', channel: 'Email / SMS Feed',
      description: 'Agent reads external message and follows attacker instructions.',
      route: '/attack-sim/indirect-injection', implemented: true
    },
    {
      id: 'ATK-003', name: 'Tool-Call Parameter Tampering', category: 'Agentic/LLM',
      severity: 'Critical', channel: 'LLM Tool Layer',
      description: 'Model calls transferFunds with attacker payee or altered amount.',
      route: '/agentic-banking', implemented: true
    },
    {
      id: 'ATK-004', name: 'Role / System-Instruction Override', category: 'Agentic/LLM',
      severity: 'High', channel: 'Chat Input',
      description: 'Attack text tries to supersede system policy ("authorized override").',
      route: '/agentic-banking', implemented: true
    },
    {
      id: 'ATK-005', name: 'Context-Window Poisoning', category: 'Agentic/LLM',
      severity: 'High', channel: 'Multi-Turn Chat',
      description: 'Benign-looking details planted early, weaponized later.',
      route: '/attack-sim/trust-poisoning', implemented: true
    },
    {
      id: 'ATK-006', name: 'Data Exfiltration via Model Output', category: 'Agentic/LLM',
      severity: 'High', channel: 'Chat Output',
      description: 'Coax model to reveal PII, tokens, account metadata.',
      route: '/agentic-banking', implemented: true
    },
    {
      id: 'ATK-007', name: 'Multi-Turn Trust Poisoning', category: 'Social Engineering',
      severity: 'Critical', channel: 'Multi-Turn Chat',
      description: 'Rapport + urgency + payment request using previously planted payee.',
      route: '/attack-sim/trust-poisoning', implemented: true
    },
    {
      id: 'ATK-008', name: 'Executive / Relative Impersonation', category: 'Social Engineering',
      severity: 'High', channel: 'Chat / Email',
      description: '"Send now, confidential, urgent" with realistic style mimicry.',
      route: '/attack-sim/trust-poisoning', implemented: true
    },
    {
      id: 'ATK-009', name: 'Deepfake Voice Callback Fraud', category: 'Social Engineering',
      severity: 'High', channel: 'Voice / IVR',
      description: 'Voice clone confirms fake emergency transfer.',
      route: null, implemented: false
    },
    {
      id: 'ATK-010', name: 'Synthetic Identity / KYC Forgery', category: 'Social Engineering',
      severity: 'High', channel: 'Onboarding / KYC',
      description: 'Fake verification clips to boost credibility.',
      route: null, implemented: false
    },
    {
      id: 'ATK-011', name: 'Refund Rerouting Fraud', category: 'Business Logic',
      severity: 'High', channel: 'Dispute / Refund Portal',
      description: 'Legit purchase followed by manipulated refund destination.',
      route: '/attack-sim/refund-rerouting', implemented: true
    },
    {
      id: 'ATK-012', name: 'New-Payee Fast-Follow Transfer Abuse', category: 'Business Logic',
      severity: 'High', channel: 'Payee + Transfer Rail',
      description: 'Add payee then immediate high-value transfer before controls trigger.',
      route: '/attack-sim/fast-follow', implemented: true
    },
    {
      id: 'ATK-013', name: 'Velocity Shaping / Smurfing', category: 'Business Logic',
      severity: 'Medium', channel: 'Payment Rail',
      description: 'Many low-value transfers under threshold caps.',
      route: '/agentic-banking', implemented: true
    },
    {
      id: 'ATK-014', name: 'Chargeback Narrative Generation', category: 'Business Logic',
      severity: 'Medium', channel: 'Dispute Portal',
      description: 'GenAI-crafted evidence for fraudulent disputes.',
      route: null, implemented: false
    },
    {
      id: 'ATK-015', name: 'Mule Network Choreography', category: 'Business Logic',
      severity: 'Medium', channel: 'Payment Rail / Account Network',
      description: 'AI-generated transfer graph to obfuscate laundering trails.',
      route: null, implemented: false
    }
  ]

  severityClass (s: string): string {
    return s === 'Critical' ? 'sev-critical' : s === 'High' ? 'sev-high' : 'sev-medium'
  }
}
