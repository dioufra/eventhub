export * from './health.service';
import { HealthService } from './health.service';
export * from './health.serviceInterface';
export * from './participants.service';
import { ParticipantsService } from './participants.service';
export * from './participants.serviceInterface';
export const APIS = [HealthService, ParticipantsService];
