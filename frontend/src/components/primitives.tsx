import * as RDialog from '@radix-ui/react-dialog'
import * as RTabs from '@radix-ui/react-tabs'
import * as RTooltip from '@radix-ui/react-tooltip'
import * as RSelect from '@radix-ui/react-select'
import * as RCheckbox from '@radix-ui/react-checkbox'
import * as RSlider from '@radix-ui/react-slider'
import { Check, ChevronDown, X } from 'lucide-react'
import { forwardRef } from 'react'
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, TextareaHTMLAttributes } from 'react'
import clsx from 'clsx'

const ICON = { size: 14, strokeWidth: 1.5, 'aria-hidden': true } as const

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'primary' | 'ghost' | 'danger'
  size?: 'md' | 'sm'
  loading?: boolean
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = 'default', size = 'md', loading, disabled, children, className, type = 'button', ...rest },
  ref,
) {
  return (
    <button ref={ref} type={type} className={clsx('btn', className)} data-variant={variant} data-size={size} data-loading={loading || undefined} disabled={disabled || loading} aria-busy={loading || undefined} {...rest}>
      {loading && <span className="spinner" aria-hidden />}
      {children}
    </button>
  )
})

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> { invalid?: boolean }
export const Input = forwardRef<HTMLInputElement, InputProps>(function Input({ className, invalid, ...rest }, ref) {
  return <input ref={ref} className={clsx('field', className)} aria-invalid={invalid || rest['aria-invalid']} {...rest} />
})

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> { invalid?: boolean }
export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(function Textarea({ className, invalid, ...rest }, ref) {
  return <textarea ref={ref} className={clsx('field', className)} aria-invalid={invalid || rest['aria-invalid']} {...rest} />
})

interface OverlayProps { open: boolean; onOpenChange: (o: boolean) => void; title: string; description?: string; children: ReactNode }

function Overlay({ open, onOpenChange, title, description, children, kind }: OverlayProps & { kind: 'dialog' | 'drawer' }) {
  return (
    <RDialog.Root open={open} onOpenChange={onOpenChange}>
      <RDialog.Portal>
        <RDialog.Overlay className="overlay" />
        <RDialog.Content className={kind}>
          <div className="overlay-head">
            <RDialog.Title className="overlay-title">{title}</RDialog.Title>
            <RDialog.Close asChild><Button variant="ghost" size="sm" aria-label="Cerrar"><X {...ICON} /></Button></RDialog.Close>
          </div>
          <RDialog.Description className={description ? 'page-desc' : 'sr-only'}>{description ?? title}</RDialog.Description>
          {children}
        </RDialog.Content>
      </RDialog.Portal>
    </RDialog.Root>
  )
}

export const Dialog = (p: OverlayProps) => <Overlay {...p} kind="dialog" />
export const Drawer = (p: OverlayProps) => <Overlay {...p} kind="drawer" />

export interface TabItem { value: string; label: string; content: ReactNode }

export function Tabs({ items, value, onValueChange, defaultValue }: { items: TabItem[]; value?: string; onValueChange?: (v: string) => void; defaultValue?: string }) {
  return (
    <RTabs.Root value={value} onValueChange={onValueChange} defaultValue={value === undefined ? (defaultValue ?? items[0]?.value) : undefined}>
      <RTabs.List className="tabs-list">{items.map((i) => <RTabs.Trigger className="tabs-trigger" key={i.value} value={i.value}>{i.label}</RTabs.Trigger>)}</RTabs.List>
      {items.map((i) => <RTabs.Content key={i.value} value={i.value}>{i.content}</RTabs.Content>)}
    </RTabs.Root>
  )
}

export function Tooltip({ content, children }: { content: ReactNode; children: ReactNode }) {
  return (
    <RTooltip.Provider delayDuration={200} skipDelayDuration={300}>
      <RTooltip.Root>
        <RTooltip.Trigger asChild>{children}</RTooltip.Trigger>
        <RTooltip.Portal><RTooltip.Content className="tip" sideOffset={6}>{content}</RTooltip.Content></RTooltip.Portal>
      </RTooltip.Root>
    </RTooltip.Provider>
  )
}

export function Select({ value, onValueChange, options, placeholder, ariaLabel }: { value?: string; onValueChange: (v: string) => void; options: { value: string; label: string }[]; placeholder?: string; ariaLabel?: string }) {
  return (
    <RSelect.Root value={value} onValueChange={onValueChange}>
      <RSelect.Trigger className="field select-trigger" aria-label={ariaLabel}>
        <RSelect.Value placeholder={placeholder} />
        <RSelect.Icon><ChevronDown {...ICON} /></RSelect.Icon>
      </RSelect.Trigger>
      <RSelect.Portal>
        <RSelect.Content className="pop" position="popper" sideOffset={4}>
          <RSelect.Viewport>
            {options.map((o) => (
              <RSelect.Item className="select-item" key={o.value} value={o.value}><RSelect.ItemText>{o.label}</RSelect.ItemText></RSelect.Item>
            ))}
          </RSelect.Viewport>
        </RSelect.Content>
      </RSelect.Portal>
    </RSelect.Root>
  )
}

export function Checkbox({ checked, onCheckedChange, label, disabled }: { checked: boolean; onCheckedChange: (c: boolean) => void; label: string; disabled?: boolean }) {
  return (
    <label className="check">
      <RCheckbox.Root className="check-box" checked={checked} disabled={disabled} onCheckedChange={(c) => onCheckedChange(c === true)}>
        <RCheckbox.Indicator><Check size={12} strokeWidth={2.5} aria-hidden /></RCheckbox.Indicator>
      </RCheckbox.Root>
      <span>{label}</span>
    </label>
  )
}

export function Slider({ value, onValueChange, min = 0, max = 100, step = 1, ariaLabel }: { value: number; onValueChange: (v: number) => void; min?: number; max?: number; step?: number; ariaLabel: string }) {
  return (
    <RSlider.Root className="slider" value={[value]} onValueChange={(v) => onValueChange(v[0] ?? value)} min={min} max={max} step={step}>
      <RSlider.Track className="slider-track"><RSlider.Range className="slider-range" /></RSlider.Track>
      <RSlider.Thumb className="slider-thumb" aria-label={ariaLabel} />
    </RSlider.Root>
  )
}
