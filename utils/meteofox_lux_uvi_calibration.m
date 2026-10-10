% compare_csv.m
%
% Usage:
%   octave --no-gui -q compare_csv.m fileREF.csv fileDUT.csv [options]
%
% Options:
%   --no-plot       Do not display graphs
%   --save DIR      Save graphs and CSV results in DIR
%   --tol SECONDS   Maximum matching tolerance
%   -h, --help      Show this help
%
% Example:
%   octave --no-gui -q compare_csv.m REF.csv DUT.csv --save results --no-plot

close all;

% Allow locating pair_by_time.m from any working directory.
scriptDir = fileparts(mfilename('fullpath'));
if ~isempty(scriptDir)
  addpath(scriptDir);
end

%% =========================================================================
% Local helper functions (declared at top)
%% =========================================================================

function [xPaired, refPaired] = pair_by_time(tRef, ref, tX, x, tol)
  % Match each reference measurement to the nearest x measurement in time.
  % tol is the maximum allowed time offset (same unit as the timestamps).

  vRef = isfinite(tRef) & isfinite(ref);
  vX = isfinite(tX) & isfinite(x);

  tRef = tRef(vRef);
  ref = ref(vRef);

  tX = tX(vX);
  x = x(vX);

  xPaired = [];
  refPaired = [];

  if isempty(tRef) || isempty(tX)
    return;
  end

  [tX, uniqueIndex] = unique(tX);
  x = x(uniqueIndex);

  if numel(tX) == 1
    index = ones(size(tRef));
  else
    index = interp1(tX, 1:numel(tX), tRef, ...
                    'nearest', 'extrap');
  end

  valid = abs(tX(index) - tRef) <= tol;

  xPaired = x(index(valid));
  refPaired = ref(valid);

  xPaired = xPaired(:);
  refPaired = refPaired(:);
end

function [bestNum, bestDen, bestError] = gain_to_fraction12(gain)
  % Find the closest fraction num/den representing the gain.
  %
  % Numerator and denominator are 12-bit unsigned:
  %   0 <= num <= 4095
  %   1 <= den <= 4095

  maxValue = 4095;

  if ~isscalar(gain) || ~isfinite(gain) || gain < 0
    error('Gain must be finite and non-negative.');
  end

  bestNum = 0;
  bestDen = 1;
  bestError = Inf;

  for den = 1:maxValue
    num = round(gain * den);

    if num < 0
      num = 0;
    elseif num > maxValue
      num = maxValue;
    end

    currentError = abs(gain - num / den);

    % In case of a tie, keep the smaller denominator.
    if currentError < bestError
      bestNum = num;
      bestDen = den;
      bestError = currentError;
    end
  end
end

function value = safeInteger(value)
  % Make NaN printable as an empty CSV field.
  if isempty(value) || ~isfinite(value)
    value = 0;
  else
    value = round(value);
  end
end

%% =========================================================================
% Command-line arguments
%% =========================================================================

usageText = [ ...
  'Usage: octave --no-gui -q compare_csv.m fileREF.csv fileDUT.csv [options]\n' ...
  '\n' ...
  'Options:\n' ...
  '  --no-plot       do not display graphs\n' ...
  '  --save DIR      save outputs in DIR\n' ...
  '  --tol SECONDS   maximum time matching tolerance\n' ...
  '                  default: 60 seconds\n' ...
  '  -h, --help      show this help\n'];

args = argv();

showPlots = true;
saveDir = '';
tolSec = 60;
files = {};

i = 1;
while i <= numel(args)
  arg = args{i};

  switch arg
    case {'-h', '--help'}
      printf(usageText);
      exit(0);

    case '--no-plot'
      showPlots = false;

    case '--save'
      if i == numel(args)
        error('Option --save requires a directory name.');
      end

      i = i + 1;
      saveDir = args{i};

    case '--tol'
      if i == numel(args)
        error('Option --tol requires a numeric value in seconds.');
      end

      i = i + 1;
      tolSec = str2double(args{i});

      if ~isfinite(tolSec) || tolSec <= 0
        error('Invalid tolerance: %s', args{i});
      end

    otherwise
      if ~isempty(arg) && arg(1) == '-'
        warning('Unknown option ignored: %s', arg);
      else
        files{end + 1} = arg;
      end
  end

  i = i + 1;
end

if numel(files) ~= 2
  fprintf(2, '%s\n', usageText);
  exit(1);
end

fileREF = files{1};
fileDUT = files{2};

if ~exist(fileREF, 'file')
  error('File not found: %s', fileREF);
end

if ~exist(fileDUT, 'file')
  error('File not found: %s', fileDUT);
end

if ~isempty(saveDir) && ~exist(saveDir, 'dir')
  [created, message] = mkdir(saveDir);

  if ~created
    error('Unable to create directory %s: %s', saveDir, message);
  end
end

%% =========================================================================
% Graph configuration
%% =========================================================================

makePlots = showPlots || ~isempty(saveDir);

if showPlots
  figVisible = 'on';
else
  figVisible = 'off';
end

% Figure size in pixels:
% [position_x, position_y, width, height]
figurePosition = [100, 100, 1600, 1000];

newFig = @(figName) figure( ...
  'name', figName, ...
  'numbertitle', 'off', ...
  'visible', figVisible, ...
  'position', figurePosition);

%% =========================================================================
% Read headers
%% =========================================================================

fid = fopen(fileREF, 'r');
if fid < 0
  error('Unable to open %s', fileREF);
end

headerLine = fgetl(fid);
fclose(fid);

if ~ischar(headerLine)
  error('Missing header in %s', fileREF);
end

header = strtrim(strsplit(headerLine, ','));
nCols = numel(header);

%% =========================================================================
% Read data
%% =========================================================================

% Empty cells are converted to NaN.
REF = dlmread(fileREF, ',', 1, 0, 'emptyvalue', NaN);
DUT = dlmread(fileDUT, ',', 1, 0, 'emptyvalue', NaN);

% Ensure same number of columns.
if columns(REF) < nCols
  REF(:, end + 1:nCols) = NaN;
end

if columns(DUT) < nCols
  DUT(:, end + 1:nCols) = NaN;
end

if columns(REF) > nCols
  REF = REF(:, 1:nCols);
end

if columns(DUT) > nCols
  DUT = DUT(:, 1:nCols);
end

%% =========================================================================
% File names
%% =========================================================================

[~, nameREF, extREF] = fileparts(fileREF);
[~, nameDUT, extDUT] = fileparts(fileDUT);

labelREF = [nameREF extREF];
labelDUT = [nameDUT extDUT];

%% =========================================================================
% Find required columns
%% =========================================================================

getColumn = @(name) find(strcmp(header, name), 1);

requiredColumns = {
  'time',
  'si1133_lux',
  'ltr390_lux',
  'veml6031_lux',
  'si1133_uvi',
  'ltr390_uvi',
  'guva_uvi_mv'
};

for k = 1:numel(requiredColumns)
  if isempty(getColumn(requiredColumns{k}))
    error('Missing column in CSV: %s', requiredColumns{k});
  end
end

colTime = getColumn('time');
colSi1133Lux = getColumn('si1133_lux');
colLtr390Lux = getColumn('ltr390_lux');
colVemlLux = getColumn('veml6031_lux');
colSi1133Uvi = getColumn('si1133_uvi');
colLtr390Uvi = getColumn('ltr390_uvi');
colGuvaUviMv = getColumn('guva_uvi_mv');

%% =========================================================================
% Convert Unix timestamps to elapsed hours
%% =========================================================================

rawTimeREF = REF(:, colTime);
rawTimeDUT = DUT(:, colTime);

validTimeREF = isfinite(rawTimeREF);
validTimeDUT = isfinite(rawTimeDUT);

if ~any(validTimeREF)
  error('No valid timestamps in %s.', fileREF);
end

if ~any(validTimeDUT)
  error('No valid timestamps in %s.', fileDUT);
end

t0 = min([rawTimeREF(validTimeREF); rawTimeDUT(validTimeDUT)]);

timeREF = (rawTimeREF - t0) / 3600000;
timeDUT = (rawTimeDUT - t0) / 3600000;

%% =========================================================================
% Merge both files
%% =========================================================================

M = [
  ones(rows(REF), 1), REF;
  2 * ones(rows(DUT), 1), DUT
];

M = sortrows(M, 2);

mergedHeader = [{'source'}, header];

mergedFile = 'merged.csv';
fid = fopen(mergedFile, 'w');

if fid < 0
  warning('Impossible to create %s.', mergedFile);
else
  fprintf(fid, '%s\n', strjoin(mergedHeader, ','));
  fclose(fid);

  dlmwrite(mergedFile, M, ...
           '-append', ...
           'delimiter', ',', ...
           'precision', '%.10g');
end

%% =========================================================================
% Specific comparisons
%% =========================================================================

comparisons(1).title = 'Enclosure calibration: DUT SI1133 LUX vs REF SI1133 LUX';
comparisons(1).times = {timeREF, timeDUT};
comparisons(1).values = {
  REF(:, colSi1133Lux),
  DUT(:, colSi1133Lux)
};
comparisons(1).labels = {labelREF, labelDUT};

comparisons(2).title = 'Enclosure calibration: DUT SI1133 UVI vs REF SI1133 UVI';
comparisons(2).times = {timeREF, timeDUT};
comparisons(2).values = {
  REF(:, colSi1133Uvi),
  DUT(:, colSi1133Uvi)
};
comparisons(2).labels = {labelREF, labelDUT};

comparisons(3).title = 'Sensors LUX calibration: SI1133 vs LTR390 vs VEML6031';
comparisons(3).times = {timeREF, timeREF, timeREF};
comparisons(3).values = {
  REF(:, colSi1133Lux),
  REF(:, colLtr390Lux),
  REF(:, colVemlLux)
};
comparisons(3).labels = {
  'si1133_lux_REF',
  'ltr390_lux_REF',
  'veml6031_lux_REF'
};

comparisons(4).title = 'Sensors UVI calibration: SI1133 vs LTR390';
comparisons(4).times = {timeREF, timeREF};
comparisons(4).values = {
  REF(:, colSi1133Uvi),
  REF(:, colLtr390Uvi)
};
comparisons(4).labels = {
  'si1133_uvi_REF',
  'ltr390_uvi_REF'
};

comparisons(5).title = 'GUVA transfer function: Voltage vs SI1133 UVI';
comparisons(5).times = {timeREF, timeREF};
comparisons(5).values = {
  REF(:, colSi1133Uvi),
  REF(:, colGuvaUviMv)
};
comparisons(5).labels = {
  'si1133_uvi_REF',
  'guva_uvi_mv_REF'
};

%% =========================================================================
% Plot temporal comparisons
%% =========================================================================

colors = [
  0.10 0.40 0.80;  % blue
  0.85 0.20 0.20;  % red
  0.10 0.60 0.25   % green
];

if makePlots
  for p = 1:numel(comparisons)

    % GUVA comparison uses two Y axes because units differ.
    if p == 5
      x1 = comparisons(p).times{1};
      y1 = comparisons(p).values{1};

      x2 = comparisons(p).times{2};
      y2 = comparisons(p).values{2};

      valid1 = isfinite(x1) & isfinite(y1);
      valid2 = isfinite(x2) & isfinite(y2);

      x1 = x1(valid1);
      y1 = y1(valid1);

      x2 = x2(valid2);
      y2 = y2(valid2);

      [x1, order1] = sort(x1);
      y1 = y1(order1);

      [x2, order2] = sort(x2);
      y2 = y2(order2);

      newFig(comparisons(p).title);

      [ax, hUvi, hMv] = plotyy(x1, y1, x2, y2);

      set(hUvi, ...
          'linestyle', '-', ...
          'linewidth', 1.8, ...
          'color', colors(1, :));

      set(hMv, ...
          'linestyle', '-', ...
          'linewidth', 1.8, ...
          'color', colors(2, :));

      set(get(ax(1), 'ylabel'), ...
          'string', 'UVI', ...
          'color', colors(1, :));

      set(get(ax(2), 'ylabel'), ...
          'string', 'GUVA (mV)', ...
          'color', colors(2, :));

      xlabel(ax(1), 'Hours elapsed since first measurement');
      title(ax(1), comparisons(p).title, 'interpreter', 'none');
      grid(ax(1), 'on');

      legend([hUvi, hMv], ...
             comparisons(p).labels, ...
             'location', 'best', ...
             'interpreter', 'none');

      continue;
    end

    % Standard comparison with one Y axis.
    newFig(comparisons(p).title);
    hold on;

    handles = [];
    legendLabels = {};

    for s = 1:numel(comparisons(p).values)
      x = comparisons(p).times{s};
      y = comparisons(p).values{s};

      valid = isfinite(x) & isfinite(y);

      if any(valid)
        xValid = x(valid);
        yValid = y(valid);

        [xValid, order] = sort(xValid);
        yValid = yValid(order);

        colorIndex = min(s, rows(colors));

        h = plot(xValid, yValid, '-', ...
                 'color', colors(colorIndex, :), ...
                 'linewidth', 1.8);

        handles(end + 1) = h;
        legendLabels{end + 1} = comparisons(p).labels{s};
      end
    end

    hold off;
    grid on;

    xlabel('Hours elapsed since first measurement');
    title(comparisons(p).title, 'interpreter', 'none');

    if ~isempty(handles)
      legend(handles, legendLabels, ...
             'location', 'best', ...
             'interpreter', 'none');
    end
  end
end

%% =========================================================================
% Calibration definitions
%% =========================================================================

tol = tolSec / 3600;

% Columns:
% name, reference time, reference, DUT time, DUT value,
% label x, label reference, model
%
% Models:
%   gain : ref = gain * x
%   lin  : ref = slope * x + offset
%   poly2: ref = a*x^2 + b*x + c

cal = {
  'DUT LUX enclosure calibration', ...
    timeREF, REF(:, colSi1133Lux), ...
    timeDUT, DUT(:, colSi1133Lux), ...
    'si1133_lux_DUT', 'si1133_lux_REF', 'gain';

  'DUT UVI enclosure calibration', ...
    timeREF, REF(:, colSi1133Uvi), ...
    timeDUT, DUT(:, colSi1133Uvi), ...
    'si1133_uvi_DUT', 'si1133_uvi_REF', 'gain';

  'LTR390 LUX calibration', ...
    timeREF, REF(:, colSi1133Lux), ...
    timeREF, REF(:, colLtr390Lux), ...
    'ltr390_lux_REF', 'si1133_lux_REF', 'gain';

  'VEML6031 LUX calibration', ...
    timeREF, REF(:, colSi1133Lux), ...
    timeREF, REF(:, colVemlLux), ...
    'veml6031_lux_REF', 'si1133_lux_REF', 'gain';

  'LTR390 UVI calibration', ...
    timeREF, REF(:, colSi1133Uvi), ...
    timeREF, REF(:, colLtr390Uvi), ...
    'ltr390_uvi_REF', 'si1133_uvi_REF', 'gain';

  'GUVA transfer function', ...
    timeREF, REF(:, colSi1133Uvi), ...
    timeREF, REF(:, colGuvaUviMv), ...
    'guva_uvi_mv_REF', 'si1133_uvi_REF', 'lin'
};

%% =========================================================================
% Calibration and regressions
%% =========================================================================

calibResults = {};

printf('\n');
printf('%-30s %5s  %-40s %8s %12s\n', ...
       'Calibration', 'N', 'Model', 'R2', 'RMSE');
printf('%s\n', repmat('-', 1, 105));

for k = 1:rows(cal)

  [name, tR, ref, tX, x, xLab, refLab, model] = cal{k, :};

  [xp, rp] = pair_by_time(tR, ref, tX, x, tol);

  if numel(xp) < 2
    printf('%-30s : not enough paired points\n', name);
    continue;
  end

  % Default values.
  g = NaN;
  gMed = NaN;
  p = [NaN, NaN, NaN];

  %% Fit the selected model
  switch model

    case 'gain'
      % Least-squares line through the origin.
      g = xp \ rp;
      f = @(v) g * v;
      eqn = sprintf('ref = %.8f * x', g);

      % Robust median slope.
      nonZero = (xp ~= 0);
      ratios = rp(nonZero) ./ xp(nonZero);
      ratios = ratios(isfinite(ratios));

      if isempty(ratios)
        gMed = NaN;
        fMed = @(v) NaN(size(v));
        eqnMed = 'median gain unavailable';
      else
        gMed = median(ratios);
        fMed = @(v) gMed * v;
        eqnMed = sprintf('ref = %.8f * x (median)', gMed);
      end

    case 'lin'
      p = polyfit(xp, rp, 1);
      f = @(v) polyval(p, v);
      eqn = sprintf('ref = %.8f * x %+.8f', p(1), p(2));
      eqnMed = '';

    case 'poly2'
      if numel(xp) < 3
        printf('%-30s : not enough points for poly2\n', name);
        continue;
      end

      p = polyfit(xp, rp, 2);
      f = @(v) polyval(p, v);
      eqn = sprintf('ref = %.6g*x^2 %+.6g*x %+.6g', ...
                    p(1), p(2), p(3));
      eqnMed = '';

    otherwise
      error('Unknown model: %s', model);
  end

  %% Quality of the main fit
  predicted = f(xp);
  residuals = rp - predicted;

  sumTotal = sum((rp - mean(rp)).^2);

  if sumTotal > 0
    R2 = 1 - sum(residuals.^2) / sumTotal;
  else
    R2 = NaN;
  end

  RMSE = sqrt(mean(residuals.^2));

  printf('%-30s %5d  %-40s %8.4f %12.5g\n', ...
         name, numel(xp), eqn, R2, RMSE);

  %% 12-bit fraction approximation for the gain
  numLS = NaN;
  denLS = NaN;
  errLS = NaN;

  numMed = NaN;
  denMed = NaN;
  errMed = NaN;

  if strcmp(model, 'gain')

    [numLS, denLS, errLS] = gain_to_fraction12(g);

    printf('  Least-squares gain : %d/%d = %.10f', ...
           numLS, denLS, numLS / denLS);
    printf('  error = %.6g\n', errLS);

    if isfinite(gMed)
      [numMed, denMed, errMed] = gain_to_fraction12(gMed);

      printf('  Median gain        : %d/%d = %.10f', ...
             numMed, denMed, numMed / denMed);
      printf('  error = %.6g\n', errMed);
    else
      printf('  Median gain        : unavailable\n');
    end

  elseif strcmp(model, 'lin')

    if isfinite(p(1)) && p(1) >= 0
      [numLS, denLS, errLS] = gain_to_fraction12(p(1));

      printf('  Slope as 12-bit gain: %d/%d = %.10f', ...
             numLS, denLS, numLS / denLS);
      printf('  error = %.6g\n', errLS);

      printf('  Offset to apply     : %+.10f\n', p(2));
    end
  end

  %% Store results
  result = {};
  result.name = name;
  result.N = numel(xp);
  result.model = model;
  result.equation = eqn;
  result.R2 = R2;
  result.RMSE = RMSE;
  result.gain = g;
  result.gainMedian = gMed;
  result.numLS = numLS;
  result.denLS = denLS;
  result.errLS = errLS;
  result.numMed = numMed;
  result.denMed = denMed;
  result.errMed = errMed;
  result.offset = p(2);

  calibResults{end + 1} = result;

  %% Calibration plot
  if makePlots

    newFig(['Calibration ' name]);

    hData = plot(xp, rp, 'o', ...
                 'color', [0.10, 0.40, 0.80], ...
                 'markersize', 5, ...
                 'displayname', 'paired measurements');

    hold on;

    minX = min(xp);
    maxX = max(xp);

    if minX > 0
      minPlotX = 0;
    else
      minPlotX = minX;
    end

    if maxX == minPlotX
      maxPlotX = minPlotX + 1;
    else
      maxPlotX = maxX;
    end

    xf = linspace(minPlotX, maxPlotX, 200)';

    % Least-squares or linear/poly2 fit.
    hModel = plot(xf, f(xf), '-', ...
                  'color', [0.85, 0.20, 0.20], ...
                  'linewidth', 1.8, ...
                  'displayname', eqn);

    legendHandles = [hData, hModel];
    legendLabels = {'paired measurements', eqn};

    % For gain models, add median-based curve.
    if strcmp(model, 'gain') && isfinite(gMed)
      hMedian = plot(xf, fMed(xf), '--', ...
                     'color', [0.10, 0.65, 0.20], ...
                     'linewidth', 1.8, ...
                     'displayname', eqnMed);

      legendHandles(end + 1) = hMedian;
      legendLabels{end + 1} = eqnMed;
    end

    hold off;
    grid on;

    xlabel(xLab, 'interpreter', 'none');
    ylabel(refLab, 'interpreter', 'none');

    title(sprintf('%s   R2 = %.4f', name, R2), ...
          'interpreter', 'none');

    legend(legendHandles, legendLabels, ...
           'location', 'best', ...
           'interpreter', 'none');
  end
end

%% =========================================================================
% Export calibration results
%% =========================================================================

if ~isempty(saveDir)

  resultsFile = fullfile(saveDir, 'calibration_results.csv');
  fid = fopen(resultsFile, 'w');

  if fid < 0
    warning('Unable to create %s.', resultsFile);
  else
    fprintf(fid, [ ...
      'Calibration,N,Model,Equation,R2,RMSE,' ...
      'Gain,GainMedian,' ...
      'NumeratorLS,DenominatorLS,FractionErrorLS,' ...
      'NumeratorMedian,DenominatorMedian,FractionErrorMedian,' ...
      'Offset\n']);

    for k = 1:numel(calibResults)
      r = calibResults{k};

      % Replace commas in equations to avoid CSV issues.
      equationCsv = strrep(r.equation, ',', ';');

      fprintf(fid, ...
        '%s,%d,%s,"%s",%.10g,%.10g,%.10g,%.10g,%d,%d,%.10g,%d,%d,%.10g,%.10g\n', ...
        r.name, ...
        r.N, ...
        r.model, ...
        equationCsv, ...
        r.R2, ...
        r.RMSE, ...
        r.gain, ...
        r.gainMedian, ...
        safeInteger(r.numLS), ...
        safeInteger(r.denLS), ...
        r.errLS, ...
        safeInteger(r.numMed), ...
        safeInteger(r.denMed), ...
        r.errMed, ...
        r.offset);
    end

    fclose(fid);

    printf('\nResults saved in: %s\n', resultsFile);
  end
end

%% =========================================================================
% Export figures
%% =========================================================================

figs = findobj(0, 'type', 'figure');

if ~isempty(saveDir) && ~isempty(figs)

  for k = 1:numel(figs)
    fig = figs(k);
    figName = get(fig, 'name');

    safeName = regexprep(figName, '[^A-Za-z0-9_-]+', '_');
    outputFile = fullfile(saveDir, [safeName '.png']);

    % High-resolution export.
    print(fig, outputFile, '-dpng', '-r300');
  end

  printf('%d figure(s) saved in %s\n', ...
         numel(figs), saveDir);
end

%% =========================================================================
% Clean exit
%% =========================================================================

% Clean up temporary files
if exist('merged.csv', 'file')
  delete('merged.csv');
end

if showPlots && ~isempty(figs)
  printf('Close the graph windows to finish.\n');

  while any(ishghandle(figs))
    pause(0.5);
  end
end

close all force;
drawnow;

exit(0);
