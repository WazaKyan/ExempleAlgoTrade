Bonjour,
Pour utiliser ces script, veiller à bien changer les chemin d'accès.

Voici un résumé rapide de la stratégie de Backtest (simplifié pour vous chères recruteurs)

Règles pour les opérations d'achat (Buy) :
Condition d'achat : Une position d'achat est initiée lorsque le prix de clôture ajusté (Adj Close) est supérieur à la moyenne mobile sur 200 jours (MA200),
le RSI est supérieur à RSI_NO_BUY et inférieur à RSI_LOW_BUY. Formellement, la condition est :

(df['Adj Close'] > df['MA200']) & (df['RSI'] > args.RSI_NO_BUY) & (df['RSI'] < args.RSI_LOW_BUY)
Signal d'achat : Un signal d'achat est généré lorsque la condition d'achat est vraie pour la première fois après une période sans achat.
Cela est vérifié en comparant la valeur actuelle de la colonne Buy avec sa valeur décalée d'une période (df['Buy'].shift(1)).

Date de vente : Pour chaque position d'achat, la date de vente est déterminée par la première occurrence où le RSI dépasse RSI_HIGHT_SELL après la date d'achat,
ou par la date située TIME_TO_SELL jours après l'achat si cette condition de RSI n'est pas remplie.

Règles pour les opérations de vente à découvert (Short) :
Condition de short : Une position de vente à découvert est initiée lorsque le prix de clôture ajusté (Adj Close) est inférieur à la moyenne mobile sur 200 jours pour les positions courtes (MA200_SHORT),
et que le RSI pour les positions courtes (RSI_SHORT) est supérieur à RSI_HIGHT_SELL_SHORT. La condition formelle est :

(df['Adj Close'] < df['MA200_SHORT']) & (df['RSI_SHORT'] > args.RSI_HIGHT_SELL_SHORT)
Signal de short : Un signal de vente à découvert est généré lorsque la condition de short est vraie pour la première fois après une période sans short. 
Cela est vérifié en comparant la valeur actuelle de la colonne Short avec sa valeur décalée d'une période (df['Short'].shift(1)).

Date de couverture : Pour chaque position de vente à découvert, la date de couverture est déterminée par la première occurrence où le RSI pour les positions courtes (RSI_SHORT)
est inférieur à RSI_LOW_BUY_SHORT et supérieur à RSI_NO_BUY_SHORT après la date de short, ou par la date située TIME_TO_SELL_SHORT jours après le short si cette condition de RSI n'est pas remplie.
