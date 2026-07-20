import { ChangeDetectionStrategy, Component, ElementRef, effect, input, viewChild } from '@angular/core';
import * as QRCode from 'qrcode';

/**
 * Wrapper fino sobre el paquete "qrcode" (sin dependencia de un binding
 * Angular-específico) — genera el QR en un <canvas> a partir del
 * ticket_code. El control de tamaño/estilo queda en nuestras manos.
 */
@Component({
  selector: 'app-qr-code',
  standalone: true,
  template: `<canvas #canvas></canvas>`,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class QrCode {
  readonly value = input.required<string>();
  readonly size = input<number>(160);

  private readonly canvasRef = viewChild.required<ElementRef<HTMLCanvasElement>>('canvas');

  constructor() {
    effect(() => {
      const value = this.value();
      const size = this.size();
      const canvas = this.canvasRef().nativeElement;

      QRCode.toCanvas(canvas, value, { width: size, margin: 1 }).catch((err) => {
        console.error('No se pudo generar el QR', err);
      });
    });
  }
}
