export * from './health.service';
import { HealthService } from './health.service';
export * from './health.serviceInterface';
export * from './registrations.service';
import { RegistrationsService } from './registrations.service';
export * from './registrations.serviceInterface';
export const APIS = [HealthService, RegistrationsService];
