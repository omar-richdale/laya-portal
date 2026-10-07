"""Keep the Laya 0.3.22 reference forward pass on CUDA without its CPU retry.

Only the device-error policy changes. Tokenization, model architecture, answer
heads, temperatures and output conversion remain in the upstream Agent.
Recheck this adapter before changing the pinned Laya version.
"""
from importlib.metadata import version

import torch
from laya.agent import Agent, _amp_context


class GPUOnlyAgent(Agent):
    def __init__(self, *args, **kwargs):
        if version("laya") != "0.3.22":
            raise RuntimeError("GPUOnlyAgent requires the reviewed Laya 0.3.22 runtime")
        super().__init__(*args, device="cuda:0", fast=False, compile=False, **kwargs)
        if self.device.type != "cuda" or any(p.device.type != "cuda" for p in self.model.parameters()):
            raise RuntimeError("The checkpoint could not be placed on CUDA; CPU inference is disabled")

    def _infer(self, batch):
        """Match the upstream CUDA run() branch, propagating every GPU error."""
        if self.device.type != "cuda":
            raise RuntimeError("CPU inference is disabled")
        enabled = self._amp_enabled_for(batch["input_ids"].shape[0])
        with _amp_context(self.device, self.dtype, enabled):
            return self.model(
                batch["input_ids"].to(self.device),
                batch["attention_mask"].to(self.device),
                batch["marker_pos"].to(self.device),
                batch["marker_mask"].to(self.device),
                batch["qtype"].to(self.device),
            )
