import "@testing-library/jest-dom";

// ResizeObserver absent dans jsdom (utilisé par recharts et GameGrid)
global.ResizeObserver = class ResizeObserver {
  observe() { }
  unobserve() { }
  disconnect() { }
};

// Canvas 2D absent dans jsdom :mock minimal des méthodes utilisées
const mockCtx = {
  fillStyle: "",
  strokeStyle: "",
  lineWidth: 1,
  shadowBlur: 0,
  shadowColor: "",
  font: "",
  textAlign: "",
  save: () => { },
  restore: () => { },
  fillRect: () => { },
  clearRect: () => { },
  beginPath: () => { },
  moveTo: () => { },
  lineTo: () => { },
  arc: () => { },
  fill: () => { },
  stroke: () => { },
  fillText: () => { },
  roundRect: () => { },
  quadraticCurveTo: () => { },
  createLinearGradient: () => ({
    addColorStop: () => { },
  }),
};

HTMLCanvasElement.prototype.getContext = () => mockCtx;
