import { propertyService } from '@/services/PropertyService';
import { Preference } from '@qrent/shared';
import { NextFunction, Request, Response } from 'express';
import _ from 'lodash';

export class PropertyController {
  async handleSubscribeProperty(req: Request, res: Response, next: NextFunction) {
    const propertyId = parseInt(req.params.propertyId);
    const userId = req.user!.userId;
    const result = await propertyService.subscribeToProperty(userId, propertyId);

    res.json(result);
  }

  async handleUnsubscribeProperty(req: Request, res: Response, next: NextFunction) {
    const propertyId = parseInt(req.params.propertyId);
    const userId = req.user!.userId;
    const result = await propertyService.unsubscribeFromProperty(userId, propertyId);

    res.json(result);
  }

  async getSubscriptions(req: Request, res: Response, next: NextFunction) {
    const userId = req.user!.userId;

    // Extract locale from headers, similar to tRPC context
    const localeHeader = req.headers['x-locale'] as string;
    const acceptLanguage = req.headers['accept-language'];

    let locale = 'en'; // default
    if (localeHeader && ['en', 'zh'].includes(localeHeader)) {
      locale = localeHeader;
    } else if (acceptLanguage) {
      const preferredLocale = acceptLanguage.split(',')[0]?.split('-')[0];
      if (preferredLocale && ['en', 'zh'].includes(preferredLocale)) {
        locale = preferredLocale;
      }
    }

    const result = await propertyService.fetchSubscriptions(userId, locale);

    res.json(result);
  }

  async fetchProperty(req: Request, res: Response) {
    let preferences: Preference & { page: number; pageSize: number } = req.body;

    if (req.user?.userId) {
      preferences.userId = req.user.userId;
    }
    await propertyService.createPreference(
      _.omit(preferences, ['page', 'pageSize', 'orderBy', 'publishedAt']) as Preference
    );

    const properties = await propertyService.getPropertiesByPreferences(preferences);
    res.json(properties);
  }
}

export const propertyController = new PropertyController();
