import shutil
import subprocess
from pathlib import Path

import pytest


def test_interim_speech_is_visible_before_recognition_ends():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node.js is not installed')
    component = Path(__file__).resolve().parents[1] / 'speech_input' / 'index.html'
    script = r'''
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const html = fs.readFileSync(process.argv[1], 'utf8');
const code = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const field = {value: 'Existing question'};
const button = {setAttribute() {}, addEventListener(type, fn) { this.click = fn; }};
const status = {};
const messages = [];
let instance;
class Recognition { constructor() { instance = this; } start() { this.onstart(); } }
const context = {
  document: {getElementById: id => id === 'mic' ? button : status},
  window: {SpeechRecognition: Recognition, parent: {postMessage: msg => messages.push(msg)},
    frameElement: {closest: () => ({querySelector: () => field})},
    addEventListener(type, fn) { this.render = fn; }},
};
vm.runInNewContext(code, context);
context.window.render({data: {type: 'streamlit:render', args: {locale: 'en-IN', start_label: 'Start', stop_label: 'Stop'}}});
button.click();
instance.onresult({results: [[{transcript: 'leaves are'}]]});
assert.strictEqual(field.value, 'Existing question leaves are');
assert.strictEqual(messages.filter(m => m.type === 'streamlit:setComponentValue').length, 0);
instance.onresult({results: [[{transcript: 'leaves are yellow'}]]});
assert.strictEqual(field.value, 'Existing question leaves are yellow');
instance.onend();
assert.strictEqual(messages.filter(m => m.type === 'streamlit:setComponentValue').pop().value.text, 'leaves are yellow');
'''
    subprocess.run([node, '-e', script, str(component)], check=True, capture_output=True, text=True)
