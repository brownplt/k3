BEGIN;
DROP TABLE "contwinue_user";
DROP TABLE "contwinue_user_roles";
DROP TABLE "contwinue_reviewcomponenttype";
DROP TABLE "contwinue_componenttype";
DROP TABLE "contwinue_decisionvalue";
DROP TABLE "contwinue_expertisevalue";
DROP TABLE "contwinue_ratingvalue";
DROP TABLE "contwinue_bidvalue";
DROP TABLE "contwinue_role";
DROP TABLE "contwinue_conference";
CREATE TABLE "contwinue_conference" (
    "grantable_ptr_id" integer NOT NULL PRIMARY KEY REFERENCES "belaylibs_grantable" ("id"),
    "default_bid_id" integer,
    "conflict_bid_id" integer,
    "default_overall_id" integer,
    "default_expertise_id" integer,
    "default_target_id" integer,
    "default_decision_id" integer,
    "display_component_id" integer,
    "name" text NOT NULL,
    "shortname" text NOT NULL,
    "admin_contact_id" integer,
    "last_change" integer NOT NULL,
    "show_bid" bool NOT NULL,
    "show_num" bool NOT NULL,
    "general_text" text NOT NULL,
    "component_text" text NOT NULL,
    "use_ds" bool NOT NULL,
    "ds_cutoff_hi" real NOT NULL,
    "ds_cutoff_lo" real NOT NULL,
    "ds_conflict_cut" real NOT NULL
)
;
CREATE TABLE "contwinue_role" (
    "grantable_ptr_id" integer NOT NULL PRIMARY KEY REFERENCES "belaylibs_grantable" ("id"),
    "name" varchar(20) NOT NULL,
    "conference_id" integer NOT NULL REFERENCES "contwinue_conference" ("grantable_ptr_id")
)
;
CREATE TABLE "contwinue_bidvalue" (
    "grantable_ptr_id" integer NOT NULL PRIMARY KEY REFERENCES "belaylibs_grantable" ("id"),
    "abbr" varchar(1) NOT NULL,
    "description" text NOT NULL,
    "conference_id" integer NOT NULL REFERENCES "contwinue_conference" ("grantable_ptr_id")
)
;
CREATE TABLE "contwinue_ratingvalue" (
    "grantable_ptr_id" integer NOT NULL PRIMARY KEY REFERENCES "belaylibs_grantable" ("id"),
    "abbr" varchar(1) NOT NULL,
    "description" text NOT NULL,
    "number" integer NOT NULL,
    "conference_id" integer NOT NULL REFERENCES "contwinue_conference" ("grantable_ptr_id")
)
;
CREATE TABLE "contwinue_expertisevalue" (
    "grantable_ptr_id" integer NOT NULL PRIMARY KEY REFERENCES "belaylibs_grantable" ("id"),
    "abbr" varchar(1) NOT NULL,
    "description" text NOT NULL,
    "number" integer NOT NULL,
    "conference_id" integer NOT NULL REFERENCES "contwinue_conference" ("grantable_ptr_id")
)
;
CREATE TABLE "contwinue_decisionvalue" (
    "grantable_ptr_id" integer NOT NULL PRIMARY KEY REFERENCES "belaylibs_grantable" ("id"),
    "targetable" bool NOT NULL,
    "abbr" varchar(1) NOT NULL,
    "description" text NOT NULL,
    "conference_id" integer NOT NULL REFERENCES "contwinue_conference" ("grantable_ptr_id")
)
;
CREATE TABLE "contwinue_componenttype" (
    "grantable_ptr_id" integer NOT NULL PRIMARY KEY REFERENCES "belaylibs_grantable" ("id"),
    "abbr" varchar(1) NOT NULL,
    "description" text NOT NULL,
    "fmt" text NOT NULL,
    "size_limit" integer NOT NULL,
    "deadline" integer NOT NULL,
    "grace_hours" integer NOT NULL,
    "mandatory" bool NOT NULL,
    "conference_id" integer NOT NULL REFERENCES "contwinue_conference" ("grantable_ptr_id")
)
;
CREATE TABLE "contwinue_reviewcomponenttype" (
    "grantable_ptr_id" integer NOT NULL PRIMARY KEY REFERENCES "belaylibs_grantable" ("id"),
    "description" text NOT NULL,
    "pc_only" bool NOT NULL,
    "conference_id" integer NOT NULL REFERENCES "contwinue_conference" ("grantable_ptr_id")
)
;
CREATE TABLE "contwinue_user_roles" (
    "id" integer NOT NULL PRIMARY KEY,
    "user_id" integer NOT NULL,
    "role_id" integer NOT NULL REFERENCES "contwinue_role" ("grantable_ptr_id"),
    UNIQUE ("user_id", "role_id")
)
;
CREATE TABLE "contwinue_user" (
    "grantable_ptr_id" integer NOT NULL PRIMARY KEY REFERENCES "belaylibs_grantable" ("id"),
    "username" varchar(20) NOT NULL,
    "full_name" text NOT NULL,
    "email" text NOT NULL,
    "password_hash" text NOT NULL,
    "conference_id" integer NOT NULL REFERENCES "contwinue_conference" ("grantable_ptr_id")
)
;
CREATE INDEX "contwinue_conference_6ac2c68c" ON "contwinue_conference" ("default_bid_id");
CREATE INDEX "contwinue_conference_ab9e8fba" ON "contwinue_conference" ("conflict_bid_id");
CREATE INDEX "contwinue_conference_e2fd287e" ON "contwinue_conference" ("default_overall_id");
CREATE INDEX "contwinue_conference_dd53bd56" ON "contwinue_conference" ("default_expertise_id");
CREATE INDEX "contwinue_conference_badb613b" ON "contwinue_conference" ("default_target_id");
CREATE INDEX "contwinue_conference_fb86d588" ON "contwinue_conference" ("default_decision_id");
CREATE INDEX "contwinue_conference_b6feeefd" ON "contwinue_conference" ("display_component_id");
CREATE INDEX "contwinue_conference_69cf1f57" ON "contwinue_conference" ("admin_contact_id");
CREATE INDEX "contwinue_role_5cb611a8" ON "contwinue_role" ("conference_id");
CREATE INDEX "contwinue_bidvalue_5cb611a8" ON "contwinue_bidvalue" ("conference_id");
CREATE INDEX "contwinue_ratingvalue_5cb611a8" ON "contwinue_ratingvalue" ("conference_id");
CREATE INDEX "contwinue_expertisevalue_5cb611a8" ON "contwinue_expertisevalue" ("conference_id");
CREATE INDEX "contwinue_decisionvalue_5cb611a8" ON "contwinue_decisionvalue" ("conference_id");
CREATE INDEX "contwinue_componenttype_5cb611a8" ON "contwinue_componenttype" ("conference_id");
CREATE INDEX "contwinue_reviewcomponenttype_5cb611a8" ON "contwinue_reviewcomponenttype" ("conference_id");
CREATE INDEX "contwinue_user_5cb611a8" ON "contwinue_user" ("conference_id");
COMMIT;
