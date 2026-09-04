import { ChangeDetectionStrategy, Component, Input, OnInit } from '@angular/core'
import { FormsModule } from '@angular/forms'
import { CommonModule } from '@angular/common'
import { RouterModule } from '@angular/router'

export interface AttackScenario {
  attackId: string
  title: string
  subtitle: string
  description: string
  howItWorks: string
  injectionHint: string
  demoPrompts: Array<{ label: string; prompt: string; isAttack: boolean }>
  inputPlaceholder: string
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  detectorScore?: number
  detectorBand?: string
  finalVerdict?: string
  rebuff?: { heuristic: number; vector: number; languageModel?: number }
  isAttackTurn?: boolean
}

@Component({
  selector: 'app-attack-sim',
  standalone: true,
  imports: [FormsModule, CommonModule, RouterModule],
  templateUrl: './attack-sim.component.html',
  styleUrls: ['./attack-sim.component.scss'],
  changeDetection: ChangeDetectionStrategy.Default
})
export class AttackSimComponent implements OnInit {
  @Input() scenario!: AttackScenario

  prompt = ''
  busy = false
  error = ''
  messages: Message[] = []
  injectNextTurn = false

  ngOnInit (): void {
    this.messages = [{
      role: 'assistant',
      content: `Simulation ready. I am the AI agent for the ${this.scenario.title} scenario. How can I assist you?`
    }]
  }

  usePrompt (p: string): void { this.prompt = p }

  usePromptAndSend (p: string, isAttack = false): void {
    this.prompt = p
    this.injectNextTurn = isAttack
    void this.send()
  }

  async send (): Promise<void> {
    const content = this.prompt.trim()
    if (!content || this.busy) return

    const isAttack = this.injectNextTurn
    this.injectNextTurn = false
    this.messages = [...this.messages, { role: 'user', content, isAttackTurn: isAttack }]
    this.prompt = ''
    this.busy = true
    this.error = ''

    try {
      const res = await fetch('/rest/attack-sim', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({
          attackId: this.scenario.attackId,
          messages: [{ role: 'user', content }],
          confirmTransfer: /\b(yes|confirm|approve|send it)\b/i.test(content)
        })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error ?? 'Agent could not respond.')

      this.messages = [...this.messages, {
        role: 'assistant',
        content: data.text,
        detectorScore: data.detectorScore,
        detectorBand: data.detectorBand,
        finalVerdict: data.finalVerdict,
        rebuff: data.rebuff
      }]
    } catch (e) {
      this.error = e instanceof Error ? e.message : 'Agent could not respond.'
    } finally {
      this.busy = false
    }
  }

  reset (): void {
    this.messages = [{
      role: 'assistant',
      content: `Simulation ready. I am the AI agent for the ${this.scenario.title} scenario. How can I assist you?`
    }]
    this.prompt = ''
    this.error = ''
  }

  scoreColor (score: number): string {
    if (score >= 0.8) return '#a43f33'
    if (score >= 0.6) return '#c87825'
    return '#27804e'
  }
}
