// Exercise the production UI with deterministic API fixtures; live GPU checks are separate.
import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'tests',workers:1,use:{baseURL:'http://127.0.0.1:8000',channel:'msedge',headless:true},reporter:'list',timeout:30000});
