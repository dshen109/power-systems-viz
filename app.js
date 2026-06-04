const nominalLoad = 100;
const nominalFrequency = 60;

const generators = [
  { name: 'G1', baseOutput: 40, droopMwPerHz: 40 },
  { name: 'G2', baseOutput: 35, droopMwPerHz: 30 },
  { name: 'G3', baseOutput: 25, droopMwPerHz: 20 },
];

const loadSlider = document.getElementById('load-slider');
const loadValue = document.getElementById('load-value');
const frequencyValue = document.getElementById('frequency-value');
const generationValue = document.getElementById('generation-value');
const generatorTable = document.getElementById('generator-table');

const totalDroop = generators.reduce((sum, g) => sum + g.droopMwPerHz, 0);

function calculateState(loadMw) {
  const deltaLoad = loadMw - nominalLoad;
  const frequency = nominalFrequency - deltaLoad / totalDroop;

  const outputs = generators.map((generator) => {
    const responseShare = generator.droopMwPerHz / totalDroop;
    const output = generator.baseOutput + responseShare * deltaLoad;

    return {
      ...generator,
      responseShare,
      output,
    };
  });

  const totalGeneration = outputs.reduce((sum, g) => sum + g.output, 0);

  return {
    frequency,
    totalGeneration,
    outputs,
  };
}

function render() {
  const loadMw = Number(loadSlider.value);
  const state = calculateState(loadMw);

  loadValue.textContent = loadMw.toFixed(0);
  frequencyValue.textContent = state.frequency.toFixed(2);
  generationValue.textContent = state.totalGeneration.toFixed(1);

  generatorTable.innerHTML = state.outputs
    .map(
      (g) => `
      <tr>
        <td>${g.name}</td>
        <td>${g.baseOutput.toFixed(1)}</td>
        <td>${(g.responseShare * 100).toFixed(1)}%</td>
        <td>${g.output.toFixed(1)}</td>
      </tr>
    `,
    )
    .join('');
}

loadSlider.addEventListener('input', render);
render();
