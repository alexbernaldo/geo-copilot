import * as RDialog from '@radix-ui/react-dialog'
import * as RTabs from '@radix-ui/react-tabs'
import * as RTooltip from '@radix-ui/react-tooltip'
import * as RSelect from '@radix-ui/react-select'
import * as RCheckbox from '@radix-ui/react-checkbox'
import * as RSlider from '@radix-ui/react-slider'
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, TextareaHTMLAttributes } from 'react'

export const Button = (p: ButtonHTMLAttributes<HTMLButtonElement>) => <button type="button" {...p} />
export const Input = (p: InputHTMLAttributes<HTMLInputElement>) => <input {...p} />
export const Textarea = (p: TextareaHTMLAttributes<HTMLTextAreaElement>) => <textarea {...p} />

export function Dialog({ open, onOpenChange, title, children }: { open: boolean; onOpenChange: (o: boolean) => void; title: string; children: ReactNode }) {
  return (
    <RDialog.Root open={open} onOpenChange={onOpenChange}>
      <RDialog.Portal>
        <RDialog.Overlay />
        <RDialog.Content>
          <RDialog.Title>{title}</RDialog.Title>
          <RDialog.Description />
          {children}
          <RDialog.Close>Cerrar</RDialog.Close>
        </RDialog.Content>
      </RDialog.Portal>
    </RDialog.Root>
  )
}

export function Drawer({ open, onOpenChange, title, children }: { open: boolean; onOpenChange: (o: boolean) => void; title: string; children: ReactNode }) {
  return (
    <RDialog.Root open={open} onOpenChange={onOpenChange}>
      <RDialog.Portal>
        <RDialog.Overlay />
        <RDialog.Content data-drawer>
          <RDialog.Title>{title}</RDialog.Title>
          <RDialog.Description />
          {children}
          <RDialog.Close>Cerrar</RDialog.Close>
        </RDialog.Content>
      </RDialog.Portal>
    </RDialog.Root>
  )
}

export interface TabItem { value: string; label: string; content: ReactNode }

export function Tabs({ items, value, onValueChange, defaultValue }: { items: TabItem[]; value?: string; onValueChange?: (v: string) => void; defaultValue?: string }) {
  return (
    <RTabs.Root value={value} onValueChange={onValueChange} defaultValue={defaultValue ?? items[0]?.value}>
      <RTabs.List>{items.map((i) => <RTabs.Trigger key={i.value} value={i.value}>{i.label}</RTabs.Trigger>)}</RTabs.List>
      {items.map((i) => <RTabs.Content key={i.value} value={i.value}>{i.content}</RTabs.Content>)}
    </RTabs.Root>
  )
}

export function Tooltip({ content, children }: { content: ReactNode; children: ReactNode }) {
  return (
    <RTooltip.Provider>
      <RTooltip.Root>
        <RTooltip.Trigger asChild>{children}</RTooltip.Trigger>
        <RTooltip.Portal><RTooltip.Content>{content}</RTooltip.Content></RTooltip.Portal>
      </RTooltip.Root>
    </RTooltip.Provider>
  )
}

export function Select({ value, onValueChange, options, placeholder, ariaLabel }: { value?: string; onValueChange: (v: string) => void; options: { value: string; label: string }[]; placeholder?: string; ariaLabel?: string }) {
  return (
    <RSelect.Root value={value} onValueChange={onValueChange}>
      <RSelect.Trigger aria-label={ariaLabel}><RSelect.Value placeholder={placeholder} /></RSelect.Trigger>
      <RSelect.Portal>
        <RSelect.Content><RSelect.Viewport>{options.map((o) => <RSelect.Item key={o.value} value={o.value}><RSelect.ItemText>{o.label}</RSelect.ItemText></RSelect.Item>)}</RSelect.Viewport></RSelect.Content>
      </RSelect.Portal>
    </RSelect.Root>
  )
}

export function Checkbox({ checked, onCheckedChange, label }: { checked: boolean; onCheckedChange: (c: boolean) => void; label: string }) {
  return (
    <label>
      <RCheckbox.Root checked={checked} onCheckedChange={(c) => onCheckedChange(c === true)}><RCheckbox.Indicator>✓</RCheckbox.Indicator></RCheckbox.Root>
      {label}
    </label>
  )
}

export function Slider({ value, onValueChange, min = 0, max = 100, step = 1, ariaLabel }: { value: number; onValueChange: (v: number) => void; min?: number; max?: number; step?: number; ariaLabel: string }) {
  return (
    <RSlider.Root value={[value]} onValueChange={(v) => onValueChange(v[0] ?? value)} min={min} max={max} step={step}>
      <RSlider.Track><RSlider.Range /></RSlider.Track>
      <RSlider.Thumb aria-label={ariaLabel} />
    </RSlider.Root>
  )
}
