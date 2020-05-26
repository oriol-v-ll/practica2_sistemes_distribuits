# practica2_sistemes_distribuits

Repositori amb el codi de la pràctica 2 de Sistemes distribuïts

En aquest programa hi ha tres funcions per la implementació de l'algoritme d'exclusió mutua. 

master --> Funció que coordina les peticions d'escriptura dels esclaus i els va donant accès depenent del temps en que hagin fet la consulta. 

Slave --> Funció que fa de client que demana peticions d'escriptura a un recurs compartit, en auqest cas s'executa la funció de manera asíncrona fent que hi hagin un numero donat d'execucions que es llancen alhora

Main --> executa la funció master i llança N_SLAVES copies de la funció slave, junta els resultats i coproba que s'han donat els permissos corresponents.
