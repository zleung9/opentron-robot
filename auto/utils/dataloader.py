from __future__ import print_function, division
import os
import torch
import yaml
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from torch.utils.data import Dataset
from btgenerate.database.database import Database

DTYPE =  torch.double
DEVICE = torch.device("cuda:3" if torch.cuda.is_available() else "cpu")

_name_dict = {
    "1,2-dimethoxyethane": "DME",
    "1,3-dioxolane": "DOL",
    "Aluminium Oxide": "Al2O3",
    "Lithium Perchlorate": "LiClO4"
}

class AutomatDataset(Dataset):
    def __init__(self, df=None, database:str="", table:str=""):
        self.database = None
        self.table = None
        self._df = df
        if not df:
            self.get_data(database=database, table=table)
        
    @property
    def dataframe(self):
        return self._df.copy()
    
    def get_data(self, database:str=None, table:str=None):
        try:
            df=Database(db=database).pull(table=table)
        except:
            raise
        else:
            self._df = df.copy()
            self.database = database
            self.table = table
            

class ChemicaltDataset(AutomatDataset):
    
    def __init__(self, df:pd.DataFrame=None):
        super().__init__(df=df, database="mars_db", table="chemical_input")
        self.map_names() # map names by default

    def __len__(self):
        return len(self._df)

    def __getitem__(self, idx=None):    
        return self._df.loc[idx, :]
    
    
    @property
    def chemical_names(self):
        return self._df["chemical"].tolist()

    
    def find_by_space(self, chemicals, property="MW"):
        """ Return a list of properties (e.g. MW, state) for a list of chemicals.
        The returned valuses are in the same order of the given chemicals.
        """
        if type(chemicals) is str:
            chemicals = [chemicals]
        _df = self._df.loc[self._df["chemical"].isin(chemicals)]
        _df = _df.set_index("chemical").loc[chemicals] # make sure the order is right
        property_values = list(_df[property])
        if len(property_values) == 1:
            property_values = property_values[0]
        return property_values


    def constraint(self, chemicals, state="liquid", threshold=0, limit="hi"):
        """Return the constraint for the amount of given state.
        The returned constraints are consistent with the form taken by `optimize_acqf` in Botorch.
        See https://botorch.org/api/_modules/botorch/optim/optimize.html#OptimizeAcqfInputs for more
        infromation
        Parameters
        ----------
        :param chemicals: a list chemicals that composes the sub-space
        :param state: str, the state for this constraint
        :param threshold: float, the limit of the amount of the given state
        :param limit: str. One of "hi" (upper limit), "lo" (lower limit), or "eq" (equality)
        """

        name = f"{limit}_{state}"
        if state == "carbonate":
            states = self.find_by_space(chemicals, property="chemical_tag")
        else:
            states = self.find_by_space(chemicals, property="state")
        states = np.array(states)
        state_indices = np.where(states == state)[0]
        coefficients = np.ones(len(state_indices))
        if limit=="hi":
            coefficients = (-1) * coefficients
            threshold = (-1) * threshold
        constraint = (
            torch.tensor(state_indices, dtype=int),
            torch.tensor(coefficients, dtype=DTYPE),
            torch.tensor(threshold, dtype=DTYPE)
        )
        return name, constraint


    def generate_constraint(self, chemicals, path=None, reduce=True):
        """Load the constraint configuration file and generate a list of constraints accordingly.
        """
        if path is None:
            path = os.path.join(os.path.dirname(__file__), "constraint.yaml")
        with open(path, "r") as f:
            config = yaml.safe_load(f)
        dim = len(chemicals)
        equality_constraints = [
            (
                "eq: sum_to_one",
                (
                    torch.arange(dim, dtype=int), 
                    torch.ones(dim, dtype=DTYPE), 
                    torch.tensor(1, dtype=DTYPE)
                )
            )
        ]
        inequqlity_constraints = [
            self.constraint(chemicals, state="lithium", threshold=config["li_max"], limit="hi"),
            self.constraint(chemicals, state="liquid", threshold=config["l_min"], limit="lo"),
            self.constraint(chemicals, state="liquid", threshold=config["l_max"], limit="hi"),
            self.constraint(chemicals, state="additive", threshold=config["add_max"], limit="hi"),
            self.constraint(chemicals, state="powder", threshold=config["pwdr_min"], limit="lo"),
            self.constraint(chemicals, state="powder", threshold=config["pwdr_max"], limit="hi"),
            self.constraint(chemicals, state="carbonate", threshold=config["carbonate_max"], limit="hi"),
        ]

        constraints = equality_constraints + inequqlity_constraints
        # remove empty constraints
        if reduce:
            constraints = [c for c in constraints if len(c[1][0]) > 0]
        return constraints

    def check_constraint(self, x, constraints, show_value=False):
        """Check if a data point is within all constraints.
        x: shape (N, M) where N is the number of data points and M is the dimension.
        constraints: a list of constraints generated by `self.generate_constraints`.
        show_value: show the value of each category instead of showing whether a constraint is met.
        Return:
        within_constraints: A pandas dataframe of booleans showing whether each data point
        are within each constrint.
        NOTE: input `x` has to be generated by BO process using `constraints`. There is no efficient
        way of forcing this requirement, so jsut keep in mind!
        """
        x = torch.tensor(x) # make sure x is a Tensor because constraints are of Tensor type. 

        within_constraints = []
        for constraint in constraints:
            name, (index, coeff, target) = constraint
            values = torch.sum(x[..., index] * coeff, axis=1)
            if name.startswith("eq:"):
                    within_constraint = torch.tensor([torch.allclose(value, target) for value in values])
            else:
                within_constraint = (torch.sum(x[..., index] * coeff, axis=1) > target)
            
            if show_value:
                # in cases of "<", values have been turned negative to preserve ">"
                values = values if target > 0 else -1 * values 
                within_constraints.append(values)
            else:
                within_constraints.append(within_constraint)

        within_constraints_df = pd.DataFrame(
            data=torch.stack(within_constraints, axis=0).T, 
            columns=[c[0] for c in constraints]
        )
        return within_constraints_df
    

    def map_names(self, name_dict:dict=None, inplace=True):
        """ Rename the main dataframe in the dataset according to `name_dict`.
        Parameters
            name_dict:  python dictionary. If `None` use the internal `_name_dict`.
        Returns
            dataframe: The renamed dataframe. 
        """
        global _name_dict
        df_copy = self._df.copy()
        if name_dict is not None:
            _name_dict = name_dict
        
        for old_name, new_name in _name_dict.items():
            df_copy.loc[df_copy["chemical"] == old_name, "chemical"] = new_name        

        if inplace:
            # Update chemical names
            for old, new in _name_dict.items():
                if old in self.chemical_names:
                    self.chemical_names.remove(old)
                    self.chemical_names.append(new)
            # Update dataframe
            self._df = df_copy
        else:
            return df_copy

class RecipeDataset(AutomatDataset):
    """The base model of pandas dataframe tailored for Automat Solutions, Inc.
    """
    def __init__(self, df:pd.DataFrame=None, database:str="", table:str=""):
        super().__init__(df=df, database=database, table=table)
        self.map_names() # standardize column names and chemical names

    @property
    def dataframe(self):
        return self._df.copy()

    def __len__(self):
        return len(self._df)

    def __getitem__(self, idx=None):    
        return self._df.loc[idx, :]

    @property
    def info_columns(self):
        raise NotImplementedError("Must define self.info_columns!")

    @property
    def chemical_names(self):
        """ Return column names that are chemicals
        """
        return self._df.columns[~self._df.columns.isin(self.info_columns)].tolist()
    
    @property
    def chemicals(self):
        df_copy = self.dataframe.fillna(0)
        return df_copy.loc[:, self.chemical_names]
    
    @property
    def electrolyte_ids(self):
        df_copy = self._df.copy()
        return df_copy.loc[:, self.electrolyte_id_col]

    @property
    def targets(self):
        """Return the target names if present in the table.
        'Cycles' is considered as a target because somethimes it is more useful than 'LCE'.
        """
        _targets = ["Cycles", "LCE", "Conductivity", "Voltage"]
        return [t for t in _targets if t in self.info_columns]
    
    def map_names(self, name_dict:dict=None, inplace=True):
        """ Rename the main dataframe in the dataset according to `name_dict`.
        Parameters
            name_dict:  python dictionary. If `None` use the internal `_name_dict`.
        Returns
            dataframe: The renamed dataframe. 
        """
        global _name_dict
        df_copy = self._df.copy()

        if "electrolyte_id" in df_copy.columns:
            self.electrolyte_id_col = "electrolyte_id"
        elif "Electrolyte ID" in df_copy.columns:
            self.electrolyte_id_col = "Electrolyte ID"
        else:
            self.electrolyte_id_col = None

        if name_dict is not None:
            _name_dict = name_dict
        df_copy.rename(columns=_name_dict, inplace=True)
        if inplace:
            # Update chemical names
            for old, new in _name_dict.items():
                if old in self.chemical_names:
                    self.chemical_names.remove(old)
                    self.chemical_names.append(new)
            # Update dataframe
            self._df = df_copy
        else:
            return df_copy

    def normalize_components(self, by="total_mass(g)", inplace=False):
        _df = self._df.copy()
        total_mass = _df[self.chemical_names].sum(axis=1).to_numpy().reshape(-1, 1)
        components = _df[self.chemical_names].to_numpy()
        normalized_components = components / total_mass
        if by is not None:
            _df[by] = 1
        _df[self.chemical_names] = normalized_components
        if inplace:
            self._df = _df
        else:
            return _df.fillna(0)

    def find_by_component(self, space, sub_space=False, super_space=False, target="LCE"):
        """ If `sub_space`, select all recipies that contain at least the given space, otherwise
        the recipes that contain at most the given space.
        If not `inclusive`, all components in `space` should be non-zero, otherwise subspaces of 
        `space` is also selected. Only works if `sub_space` is `False`.
        """
        _df = self.dataframe.fillna(0)
        present_chemicals = [space] if type(space) is str else list(space)
        absent_chemicals = [c for c in self.chemical_names if c not in space]
        select1 = (_df.loc[:, absent_chemicals] == 0).all(axis=1) # contains sub_space
        select2 = (_df.loc[:, present_chemicals] > 0).all(axis=1) # contains super_space
        if sub_space: # recipes that contain at least the given space
            select = select1
        elif super_space: # recipes that contain at most the given space
            select = select2
        else: # recipes that contain exactly the given space (all should be non-zero)
            select = select1 & select2
        eids = self.electrolyte_ids.loc[select].tolist()
        return self.find_by_eid(eids, target=target)

    def find_by_eid(self, electrolyte_ids, show_space=False, target="LCE"):
        """Given a list of electrolyte ID's, return only their non-zero components, with LCE.
        If `show_space` is `True`, return the the chemical names of the common space.
        """
        if type(electrolyte_ids) is str:
            electrolyte_ids = [electrolyte_ids]
        _df = self.dataframe.fillna(0)
        indices = _df.index[self.electrolyte_ids.isin(electrolyte_ids)]
        all_chemicals = self.chemicals.loc[indices]
        absent_chemicals = all_chemicals.columns[(all_chemicals == 0).all(axis=0)].tolist()
        present_chemicals = [c for c in self.chemical_names if c not in absent_chemicals]
        if show_space:
            return present_chemicals
        if target == "all":
            target = self.targets
        elif type(target) is str or target is None:
            target =  [target]
        target = [t for t in target if t in self.info_columns]
        df_reduced = pd.concat(
            [
                self.electrolyte_ids.loc[indices],
                # Only chemicals in presence.
                self.chemicals.loc[indices, ~all_chemicals.columns.isin(absent_chemicals)],
                _df.loc[indices, target]
            ], axis=1
        )
        return df_reduced

    def find_similar(
            self, 
            electrolyte_id, 
            tolerance=0.1, 
            ignore_value=False, 
            sub_space=False,
            targets=None
        ):
        """ For a given electrolyte ID, find all electrolytes that have the similar composition
        up to a tolerance in difference. If `by_space` is `True`, then find all electrolytes
        that fall in the same chemical sub-space disregarding the compositional difference.
        `tolerance` is a dictonary of "{chemical: tolerance}" allowing the user to specify the
        tolerance for each chemical. If `tolearnce` is a single number, then it applies to all
        chemicals.
        """
        df_reduced = self.find_by_eid(electrolyte_id, target=None)
        space = [c for c in df_reduced.columns if c not in self.info_columns]
        similar_space = self.find_by_component(space, sub_space=sub_space, target=targets)
        if ignore_value:
            return similar_space
        if type(tolerance) is float: # convert universal tolerance to chemical specific 
            tolerance = {c: tolerance for c in space}
        similar_recipes = []
        base = df_reduced.iloc[0]
        for idx, row in similar_space.iterrows():
            # caculate teh percentage difference of each chemicals 
            for chemical, t in tolerance.items():
                percentage_diff = abs(row[chemical] - base[chemical]) / base[chemical]
                if percentage_diff > t: # all differences should be smaller than tolerance
                    break
            else: # if loop finished, that means the recipe is similar to base
                similar_recipes.append(similar_space.loc[[idx]])
        if len(similar_recipes) == 0:
            similar_recipes = df_reduced
        else:
            similar_recipes = pd.concat(similar_recipes, axis=0)
        return similar_recipes


    def parallel_plot(
            self, 
            electrolyte_ids, 
            target="LCE", 
            title=None, 
            legend=True,
            fig=None
        ):
        """Generate a parallel plot of non-zero components and LCE given a list of electrolyte ID's.
        """
        _df = self.find_by_eid(electrolyte_ids, target=target)
        if fig is None:
            fig, ax = plt.subplots(figsize=(_df.shape[1]-1, 4))
        else:
            ax = fig.get_axes()[0]
        pd.plotting.parallel_coordinates(
            _df, 
            class_column=self.electrolyte_id_col, 
            ax=ax,
            colormap="tab10"
        )
        ax.set_title(title)
        ax.set_ylim([0,1])
        ax.legend(loc="best", ncol=6, fontsize=8)
        if not legend:
            ax.legend().remove()
        plt.close()
        return fig
    


class ManualMaterialsDataset(RecipeDataset):
    
    def __init__(self, df:pd.DataFrame=None):
        super().__init__(df=df, database="mars_db", table="manual_materials")
        self._df["note"] = self._df["note"].apply(lambda x: str(x, "UTF-8"))

    @property
    def info_columns(self):
        return [
            'generation_id', 'electrolyte_id', 'note', 'generation_project', 'experiment',
            'generation_method', 'total_mass(g)',
        ]
    

class LiquidMasterTableDataset(RecipeDataset):
    def __init__(self, df:pd.DataFrame=None):
        super().__init__(df=df, database="FMT", table="Liquid Master Table")


    @property
    def info_columns(self):
        return [ # columns except chemicals
            'Electrolyte ID', 'lab_batch', 'note', 'total_mass(g)', 'generation_method', 
            'generation_project', 'experiment', 'Conductivity', 'Voltage', 'Cycles', 'LCE', 
            'Initial Li efficiency', 'generation_id', 'Predicted Conductivity', 
            'Predicted Voltage', 'Predicted LCE'
        ]
    
    def export_data(self, electrolyte_ids=None, target="LCE"):
        if electrolyte_ids is not None:
            _df = self.find_by_eid(list(electrolyte_ids), target="all")
        chemicals = [c for c in _df.columns if c in self.chemical_names]
        _df.dropna(axis=0, how="any", subset=target, inplace=True)
        X = torch.from_numpy(_df.loc[:, chemicals].to_numpy(dtype=float))
        y = torch.from_numpy(_df.loc[:, target].to_numpy(dtype=float))
        return X, y


class BoExpMaterialsDataset(RecipeDataset):
    def __init__(self, df:pd.DataFrame=None):
        super().__init__(df=df, database="bo_experiments", table="exp_materials")
        
        # Override `electrolyte_id_col` with "generation_id" because they are ML generated. 
        self.electrolyte_id_col = "generation_id"

    @property
    def info_columns(self):
        return ['generation_id', 'electrolyte_id', 'generation_method',
       'generation_project', 'experiment', 'model', 'eval_num',
       'generation_batch', 'generation_date', 'total_mass(g)', 
       'number_of_input', 'Lithium', 'Liquid', 'Additive', 'Powder',
       'max_cyc1_disCh', 'max_cyc1_eff', 'max_cyc40_disCh_retention', 'score',
       'chem_score', 'Cycles', 'LCE', 'Conductivity', 'Voltage', 'note']
    

class SDWFDataset(RecipeDataset):
    def __init__(self, df:pd.DataFrame=None):
        super().__init__(df=df, database="AI_self-driving_workflow", table="measured_cond")

    @property
    def info_columns(self):
        return ["unique_id", "Composition_id", "ml_id", "measured_conductivity"]
    


if __name__ == "__main__":
    # run:
    # >>> export QT_QPA_PLATFORM=offscreen 
    ds_lmt = LiquidMasterTableDataset()
    ds_lmt.normalize_components(inplace=True)
    print(ds_lmt.find_similar("21-7-583", space_only=True))